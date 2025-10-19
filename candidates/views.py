from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.utils import timezone
import logging

from .models import (
    Skill, Candidate, CandidateProfile, CandidateSkill,
    Education, WorkExperience, Application, Interview
)
from .serializers import (
    SkillSerializer, CandidateListSerializer, CandidateDetailSerializer,
    CandidateCreateUpdateSerializer, CandidateProfileSerializer,
    CandidateSkillSerializer, EducationSerializer, WorkExperienceSerializer,
    ApplicationListSerializer, ApplicationDetailSerializer,
    ApplicationCreateSerializer, InterviewSerializer,
    InterviewCreateUpdateSerializer
)
from services.hr_agent_services import (
    ConciergeService, SkillParserService, JobMatcherService, InterviewerCopilotService
)

logger = logging.getLogger(__name__)


class SkillViewSet(viewsets.ModelViewSet):
    """スキルViewSet"""

    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'category', 'created_at']
    filterset_fields = ['category']

    @action(detail=False, methods=['get'])
    def categories(self, request):
        """スキルカテゴリ一覧を取得"""
        categories = [
            {'value': choice[0], 'label': choice[1]}
            for choice in Skill.CATEGORY_CHOICES
        ]
        return Response(categories)


class CandidateViewSet(viewsets.ModelViewSet):
    """候補者ViewSet"""

    queryset = Candidate.objects.select_related('user', 'profile').prefetch_related(
        'candidate_skills__skill', 'educations', 'work_experiences'
    )
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'current_position']
    ordering_fields = ['created_at', 'years_of_experience', 'expected_salary']
    filterset_fields = ['status', 'years_of_experience']

    def get_serializer_class(self):
        if self.action == 'list':
            return CandidateListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CandidateCreateUpdateSerializer
        return CandidateDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 候補者は自分の情報のみ
        if user.role == 'candidate':
            queryset = queryset.filter(user=user)

        return queryset

    @action(detail=False, methods=['get'])
    def me(self, request):
        """現在のユーザーの候補者情報を取得"""
        try:
            candidate = request.user.candidate
            serializer = CandidateDetailSerializer(candidate)
            return Response(serializer.data)
        except Candidate.DoesNotExist:
            return Response(
                {'detail': '候補者プロフィールが見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def profile(self, request, pk=None):
        """候補者のプロフィール詳細を取得"""
        candidate = self.get_object()
        try:
            profile = candidate.profile
            serializer = CandidateProfileSerializer(profile)
            return Response(serializer.data)
        except CandidateProfile.DoesNotExist:
            return Response(
                {'detail': 'プロフィールが見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post', 'put'])
    def update_profile(self, request, pk=None):
        """候補者プロフィールを更新"""
        candidate = self.get_object()
        profile, created = CandidateProfile.objects.get_or_create(candidate=candidate)
        serializer = CandidateProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def skills(self, request, pk=None):
        """候補者のスキル一覧を取得"""
        candidate = self.get_object()
        skills = candidate.candidate_skills.all()
        serializer = CandidateSkillSerializer(skills, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_skill(self, request, pk=None):
        """候補者にスキルを追加"""
        candidate = self.get_object()
        serializer = CandidateSkillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate=candidate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def educations(self, request, pk=None):
        """候補者の学歴一覧を取得"""
        candidate = self.get_object()
        educations = candidate.educations.all()
        serializer = EducationSerializer(educations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_education(self, request, pk=None):
        """候補者に学歴を追加"""
        candidate = self.get_object()
        serializer = EducationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate=candidate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'])
    def work_experiences(self, request, pk=None):
        """候補者の職歴一覧を取得"""
        candidate = self.get_object()
        experiences = candidate.work_experiences.all()
        serializer = WorkExperienceSerializer(experiences, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_work_experience(self, request, pk=None):
        """候補者に職歴を追加"""
        candidate = self.get_object()
        serializer = WorkExperienceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(candidate=candidate)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def parse_skills(self, request, pk=None):
        """
        AgentCoreを使用してスキルを解析
        履歴書テキストからスキルを抽出
        """
        candidate = self.get_object()
        resume_text = request.data.get('resume_text', '')

        if not resume_text:
            return Response(
                {'detail': '履歴書テキストが必要です。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            skill_parser = SkillParserService()
            result = skill_parser.parse_resume(
                user_id=str(request.user.id),
                resume_text=resume_text
            )

            if result.get('success'):
                return Response({
                    'message': 'スキル解析が完了しました。',
                    'result': result.get('response'),
                    'session_id': result.get('session_id'),
                    'is_mock': result.get('is_mock', False)
                })
            else:
                return Response(
                    {'detail': result.get('error', 'スキル解析に失敗しました。')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Skill parsing error: {e}")
            return Response(
                {'detail': f'エラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def career_advice(self, request, pk=None):
        """
        AgentCoreを使用してキャリアアドバイスを提供
        """
        candidate = self.get_object()
        question = request.data.get('question', '')

        if not question:
            return Response(
                {'detail': '質問内容が必要です。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # 職歴情報を取得
            work_experiences = candidate.work_experiences.all().values(
                'company_name', 'position', 'start_date', 'end_date', 'description'
            )
            career_history = list(work_experiences)

            concierge = ConciergeService()
            result = concierge.career_advice(
                user_id=str(request.user.id),
                question=question,
                career_history=career_history
            )

            if result.get('success'):
                return Response({
                    'message': 'キャリアアドバイスを生成しました。',
                    'advice': result.get('response'),
                    'session_id': result.get('session_id'),
                    'is_mock': result.get('is_mock', False)
                })
            else:
                return Response(
                    {'detail': result.get('error', 'アドバイス生成に失敗しました。')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Career advice error: {e}")
            return Response(
                {'detail': f'エラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def match_jobs(self, request, pk=None):
        """
        AgentCoreを使用して求人をマッチング
        """
        candidate = self.get_object()

        try:
            # 候補者プロフィールを構築
            # location preferenceはprofileから取得（存在しない場合はNone）
            location_pref = None
            try:
                if hasattr(candidate, 'profile') and candidate.profile:
                    location_pref = candidate.profile.preferred_location
            except Exception:
                pass

            candidate_profile = {
                'id': str(candidate.id),
                'name': f"{candidate.user.first_name} {candidate.user.last_name}",
                'email': candidate.user.email,
                'current_position': candidate.current_position,
                'years_of_experience': candidate.years_of_experience,
                'skills': list(candidate.candidate_skills.values(
                    'skill__name', 'proficiency_level', 'years_of_experience'
                )),
                'expected_salary': str(candidate.expected_salary) if candidate.expected_salary else None,
                'location_preference': location_pref
            }

            # 利用可能な求人を取得（全公開求人）
            from jobs.models import Job
            available_jobs = Job.objects.filter(status='active').values(
                'id', 'job_code', 'title', 'description', 'responsibilities',
                'qualifications', 'preferred_qualifications', 'salary_min', 'salary_max',
                'location', 'employment_type', 'experience_level'
            )
            available_jobs_list = list(available_jobs)

            job_matcher = JobMatcherService()
            result = job_matcher.match_candidate_to_jobs(
                user_id=str(request.user.id),
                candidate_profile=candidate_profile,
                available_jobs=available_jobs_list
            )

            if result.get('success'):
                return Response({
                    'message': '求人マッチングが完了しました。',
                    'matching_result': result.get('response'),  # 旧形式（後方互換性のため）
                    'data': result.get('data'),  # 新形式（構造化データ）
                    'session_id': result.get('session_id'),
                    'is_mock': result.get('is_mock', False)
                })
            else:
                error_msg = result.get('error', 'マッチングに失敗しました。')
                # AgentCoreのモデルアクセスエラーの場合、より分かりやすいメッセージを返す
                if 'runtime' in error_msg.lower() or '500' in error_msg:
                    error_msg = 'AIエージェントの準備中です。しばらく待ってから再度お試しください。（AWS Bedrockのモデルアクセスを確認中）'
                return Response(
                    {'detail': error_msg},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )

        except Exception as e:
            logger.error(f"Job matching error: {e}")
            return Response(
                {'detail': f'エラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CandidateSkillViewSet(viewsets.ModelViewSet):
    """候補者スキルViewSet"""

    queryset = CandidateSkill.objects.select_related('candidate', 'skill')
    serializer_class = CandidateSkillSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['candidate', 'skill', 'proficiency_level', 'is_primary']
    ordering_fields = ['years_of_experience', 'created_at']


class EducationViewSet(viewsets.ModelViewSet):
    """学歴ViewSet"""

    queryset = Education.objects.select_related('candidate')
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['candidate', 'degree', 'is_current']
    ordering_fields = ['start_date', 'created_at']


class WorkExperienceViewSet(viewsets.ModelViewSet):
    """職歴ViewSet"""

    queryset = WorkExperience.objects.select_related('candidate')
    serializer_class = WorkExperienceSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['candidate', 'is_current']
    ordering_fields = ['start_date', 'created_at']


class ApplicationViewSet(viewsets.ModelViewSet):
    """応募ViewSet"""

    queryset = Application.objects.select_related(
        'candidate__user', 'job', 'assigned_recruiter'
    ).prefetch_related('interviews')
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['candidate__user__email', 'job__title', 'job__job_code']
    ordering_fields = ['applied_date', 'matching_score', 'updated_at']
    filterset_fields = ['status', 'candidate', 'job']

    def get_serializer_class(self):
        if self.action == 'list':
            return ApplicationListSerializer
        elif self.action == 'create':
            return ApplicationCreateSerializer
        return ApplicationDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 候補者は自分の応募のみ
        if user.role == 'candidate':
            try:
                candidate = user.candidate
                queryset = queryset.filter(candidate=candidate)
            except Candidate.DoesNotExist:
                queryset = queryset.none()

        # リクルーターは担当応募または自分が管理する求人への応募
        elif user.role == 'recruiter':
            queryset = queryset.filter(
                Q(assigned_recruiter=user) |
                Q(job__recruiters=user) |
                Q(job__hiring_manager=user)
            ).distinct()

        return queryset

    @action(detail=False, methods=['get'])
    def my_applications(self, request):
        """自分の応募一覧を取得"""
        try:
            candidate = request.user.candidate
            applications = Application.objects.filter(candidate=candidate)
            serializer = ApplicationListSerializer(applications, many=True)
            return Response(serializer.data)
        except Candidate.DoesNotExist:
            return Response(
                {'detail': '候補者プロフィールが見つかりません。'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """応募ステータスを更新"""
        application = self.get_object()
        new_status = request.data.get('status')

        if new_status not in dict(Application.STATUS_CHOICES).keys():
            return Response(
                {'detail': '無効なステータスです。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        application.status = new_status
        application.save()

        serializer = self.get_serializer(application)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def interviews(self, request, pk=None):
        """応募に関連する面接一覧を取得"""
        application = self.get_object()
        interviews = application.interviews.all()
        serializer = InterviewSerializer(interviews, many=True)
        return Response(serializer.data)


class InterviewViewSet(viewsets.ModelViewSet):
    """面接ViewSet"""

    queryset = Interview.objects.select_related(
        'application__candidate__user', 'application__job'
    ).prefetch_related('interviewers')
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['application', 'interview_type', 'result']
    ordering_fields = ['scheduled_date', 'created_at']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return InterviewCreateUpdateSerializer
        return InterviewSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 候補者は自分の面接のみ
        if user.role == 'candidate':
            try:
                candidate = user.candidate
                queryset = queryset.filter(application__candidate=candidate)
            except Candidate.DoesNotExist:
                queryset = queryset.none()

        # 面接官は自分が担当する面接のみ
        elif user.role == 'interviewer':
            queryset = queryset.filter(interviewers=user)

        return queryset

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """今後の面接一覧を取得"""
        from django.utils import timezone
        interviews = self.get_queryset().filter(
            scheduled_date__gte=timezone.now(),
            result='pending'
        ).order_by('scheduled_date')
        serializer = self.get_serializer(interviews, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_feedback(self, request, pk=None):
        """面接フィードバックを提出"""
        interview = self.get_object()
        serializer = InterviewCreateUpdateSerializer(
            interview,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def submit_answers(self, request, pk=None):
        """
        候補者の面接回答を保存し、Agentに送信
        """
        interview = self.get_object()

        # 候補者は自分の面接の回答のみ送信可能
        if request.user.role == 'candidate':
            try:
                candidate = request.user.candidate
                if interview.application.candidate != candidate:
                    return Response(
                        {'detail': '権限がありません'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Candidate.DoesNotExist:
                return Response(
                    {'detail': '候補者情報が見つかりません'},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            import json

            answers = request.data.get('answers', {})
            questions = request.data.get('questions', [])
            session_id = request.data.get('session_id')

            if not answers:
                return Response(
                    {'detail': '回答が必要です。'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 回答をJSON形式でnotesフィールドに保存
            answers_data = {
                'questions': questions,
                'answers': answers,
                'submitted_at': timezone.now().isoformat(),
                'session_id': session_id
            }
            interview.notes = json.dumps(answers_data, ensure_ascii=False)

            # Agentに全回答を送信して評価を依頼
            if session_id:
                interviewer_copilot = InterviewerCopilotService()

                # 質問と回答のペアを整形
                qa_pairs = []
                for i, question in enumerate(questions):
                    answer = answers.get(str(i), '')
                    qa_pairs.append(f"Q{i+1}: {question.get('question_text', '')}\nA{i+1}: {answer}")

                qa_text = "\n\n".join(qa_pairs)

                # Agentに評価を依頼
                evaluation_result = interviewer_copilot.evaluate_interview_session(
                    user_id=str(request.user.id),
                    session_id=session_id,
                    qa_text=qa_text,
                    job_title=interview.application.job.title
                )

                if evaluation_result.get('success'):
                    # 評価結果をfeedbackに保存
                    interview.feedback = evaluation_result.get('response', '')
                    logger.info(f"Interview {interview.id} evaluated by Agent")

            # 面接を完了状態に更新
            interview.result = 'completed'  # 完了（評価待ち）
            interview.save()

            return Response({
                'message': '回答を送信しました。AIによる評価が完了しました。',
                'interview_id': interview.id,
                'session_id': session_id,
                'result': interview.result,
                'has_feedback': bool(interview.feedback)
            })

        except Exception as e:
            logger.error(f"Answer submission error: {e}")
            return Response(
                {'detail': f'エラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def generate_questions(self, request, pk=None):
        """
        AgentCoreを使用して面接質問を動的に生成
        """
        interview = self.get_object()

        # 候補者は自分の面接の質問のみ取得可能
        if request.user.role == 'candidate':
            try:
                candidate = request.user.candidate
                if interview.application.candidate != candidate:
                    return Response(
                        {'detail': '権限がありません'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Candidate.DoesNotExist:
                return Response(
                    {'detail': '候補者情報が見つかりません'},
                    status=status.HTTP_404_NOT_FOUND
                )

        try:
            # 求人情報を取得
            job = interview.application.job
            job_context = {
                'title': job.title,
                'description': job.description,
                'responsibilities': job.responsibilities,
                'qualifications': job.qualifications,
                'experience_level': job.get_experience_level_display(),
            }

            # 面接タイプに応じた質問生成
            interviewer_copilot = InterviewerCopilotService()
            result = interviewer_copilot.generate_interview_questions(
                user_id=str(request.user.id),
                job_role=job.title,
                interview_type=interview.interview_type,
                difficulty='medium',
                count=5,
                job_context=job_context,
                session_id=f"interview-{interview.id}-{request.user.id}"
            )

            if result.get('success'):
                import json

                # Agentからのレスポンスをパース
                response_text = result.get('response', '')
                questions_data = None

                try:
                    # レスポンスがJSON文字列の場合、パース
                    if isinstance(response_text, str):
                        # マークダウンコードブロックを削除
                        response_text = response_text.strip()
                        if response_text.startswith('```json'):
                            response_text = response_text[7:]
                        if response_text.startswith('```'):
                            response_text = response_text[3:]
                        if response_text.endswith('```'):
                            response_text = response_text[:-3]
                        response_text = response_text.strip()

                        questions_data = json.loads(response_text)
                    else:
                        questions_data = response_text

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Agent response as JSON: {e}")
                    logger.error(f"Response text: {response_text[:500]}")
                    # JSONパースに失敗した場合はエラーを返す
                    return Response(
                        {'detail': f'質問生成に成功しましたが、レスポンスの解析に失敗しました: {str(e)}'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

                return Response({
                    'message': '質問を生成しました。',
                    'questions': questions_data,  # パース済みのオブジェクト
                    'session_id': result.get('session_id'),
                    'is_mock': result.get('is_mock', False)
                })
            else:
                return Response(
                    {'detail': result.get('error', '質問生成に失敗しました。')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Question generation error: {e}")
            return Response(
                {'detail': f'エラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'])
    def evaluate_answer(self, request, pk=None):
        """
        AgentCoreを使用して面接回答を評価
        """
        interview = self.get_object()

        # 面接官のみ実行可能
        if request.user.role not in ['interviewer', 'recruiter', 'admin']:
            return Response(
                {'detail': '権限がありません'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            question = request.data.get('question', '')
            answer = request.data.get('answer', '')

            if not question or not answer:
                return Response(
                    {'detail': '質問と回答の両方が必要です。'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 求人情報を取得
            job = interview.application.job
            job_context = {
                'title': job.title,
                'description': job.description,
                'required_skills': job.required_skills
            }

            interviewer_copilot = InterviewerCopilotService()
            result = interviewer_copilot.evaluate_answer(
                user_id=str(request.user.id),
                question=question,
                answer=answer,
                job_context=job_context
            )

            if result.get('success'):
                return Response({
                    'message': '回答評価が完了しました。',
                    'evaluation': result.get('response'),
                    'session_id': result.get('session_id'),
                    'is_mock': result.get('is_mock', False)
                })
            else:
                return Response(
                    {'detail': result.get('error', '評価に失敗しました。')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Answer evaluation error: {e}")
            return Response(
                {'detail': f'エラーが発生しました: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
