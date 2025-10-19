from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Count, Avg
from django.shortcuts import get_object_or_404
import logging

from .models import Job, JobSkill, JobRequirement, MatchingResult
from .permissions import IsAuthenticatedForWrite, IsRecruiterOrReadOnly
from .serializers import (
    JobListSerializer as JobSerializer,
    JobDetailSerializer,
    JobCreateUpdateSerializer as JobCreateSerializer,
    JobSkillSerializer,
    JobRequirementSerializer,
    MatchingResultSerializer
)
from candidates.models import Candidate, Application
from services.hr_agent_services import InterviewerCopilotService
# BiasAuditorService is not implemented yet

logger = logging.getLogger(__name__)


class JobViewSet(viewsets.ModelViewSet):
    """求人ビューセット"""
    queryset = Job.objects.all()
    permission_classes = [IsAuthenticatedForWrite]  # 読み取りは誰でも、書き込みは認証必須

    def get_serializer_class(self):
        if self.action == 'create':
            return JobCreateSerializer
        elif self.action == 'retrieve':
            return JobDetailSerializer
        return JobSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        # 公開されている求人のみ表示（採用担当者は全て見られる）
        if not self.request.user.is_authenticated or \
           not hasattr(self.request.user, 'role') or \
           self.request.user.role != 'recruiter':
            queryset = queryset.filter(status__in=['active', 'open'])

        # フィルタリング
        location = self.request.query_params.get('location', None)
        if location:
            queryset = queryset.filter(location__icontains=location)

        employment_type = self.request.query_params.get('employment_type', None)
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)

        experience_level = self.request.query_params.get('experience_level', None)
        if experience_level:
            queryset = queryset.filter(experience_level=experience_level)

        # 給与範囲でフィルタリング
        min_salary = self.request.query_params.get('min_salary', None)
        if min_salary:
            queryset = queryset.filter(salary_max__gte=min_salary)

        max_salary = self.request.query_params.get('max_salary', None)
        if max_salary:
            queryset = queryset.filter(salary_min__lte=max_salary)

        # 検索
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(job_code__icontains=search)
            )

        # スキルでフィルタリング
        skills = self.request.query_params.get('skills', None)
        if skills:
            skill_ids = skills.split(',')
            queryset = queryset.filter(
                job_skills__skill__id__in=skill_ids
            ).distinct()

        return queryset.select_related('hiring_manager').prefetch_related(
            'job_skills__skill', 'requirements'
        ).order_by('-created_at')

    def perform_create(self, serializer):
        """求人作成時の処理"""
        serializer.save(hiring_manager=self.request.user)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def skills(self, request, pk=None):
        """求人のスキル要件を取得"""
        job = self.get_object()
        skills = JobSkill.objects.filter(job=job)
        serializer = JobSkillSerializer(skills, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def add_skill(self, request, pk=None):
        """求人にスキル要件を追加"""
        job = self.get_object()

        # Only hiring manager can edit
        if request.user != job.hiring_manager and request.user.role != 'admin':
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = JobSkillSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(job=job)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def requirements(self, request, pk=None):
        """求人の要件を取得"""
        job = self.get_object()
        requirements = JobRequirement.objects.filter(job=job)
        serializer = JobRequirementSerializer(requirements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request, pk=None):
        """Apply to job"""
        job = self.get_object()

        # Only candidates can apply
        if request.user.role != 'candidate':
            return Response(
                {'error': 'Only candidates can apply'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            candidate = request.user.candidate
        except Candidate.DoesNotExist:
            return Response(
                {'error': 'Please create your candidate profile first'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already applied
        if Application.objects.filter(candidate=candidate, job=job).exists():
            return Response(
                {'error': 'You have already applied to this job'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 応募作成
        cover_letter = request.data.get('cover_letter', '')
        application = Application.objects.create(
            candidate=candidate,
            job=job,
            cover_letter=cover_letter,
            status='pending'
        )

        # マッチングスコア計算（簡易版）
        matching_score = self.calculate_matching_score(candidate, job)
        application.matching_score = matching_score
        application.save()

        return Response({
            'message': 'Application submitted successfully',
            'application_id': application.id,
            'matching_score': matching_score
        }, status=status.HTTP_201_CREATED)

    def calculate_matching_score(self, candidate, job):
        """マッチングスコアを計算（簡易版）"""
        score = 0
        max_score = 100

        # スキルマッチング (40点満点)
        job_skills = job.job_skills.all()
        candidate_skills = candidate.candidate_skills.all()

        for job_skill in job_skills:
            for candidate_skill in candidate_skills:
                if job_skill.skill == candidate_skill.skill:
                    # スキルレベルに応じてスコア加算
                    if candidate_skill.proficiency_level == 'expert':
                        score += 10
                    elif candidate_skill.proficiency_level == 'advanced':
                        score += 7
                    elif candidate_skill.proficiency_level == 'intermediate':
                        score += 5
                    else:
                        score += 3
                    break

        # 経験年数マッチング (30点満点)
        if job.experience_level == 'junior' and candidate.years_of_experience <= 3:
            score += 30
        elif job.experience_level == 'mid' and 3 <= candidate.years_of_experience <= 7:
            score += 30
        elif job.experience_level == 'senior' and candidate.years_of_experience >= 7:
            score += 30
        elif job.experience_level == 'lead' and candidate.years_of_experience >= 10:
            score += 30

        # 給与期待値マッチング (30点満点)
        if candidate.expected_salary:
            if job.salary_min <= candidate.expected_salary <= job.salary_max:
                score += 30
            elif candidate.expected_salary < job.salary_min:
                score += 20  # 期待値が低い場合は部分点
            elif candidate.expected_salary > job.salary_max * 1.2:
                score += 0  # 期待値が高すぎる場合は0点
            else:
                score += 10  # わずかに高い場合は部分点

        # 100点満点に正規化
        return min((score / max_score) * 100, 100)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def applications(self, request, pk=None):
        """求人への応募一覧を取得"""
        job = self.get_object()

        # Only hiring manager and recruiters can view
        if request.user != job.hiring_manager and request.user.role not in ['recruiter', 'admin']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        applications = Application.objects.filter(job=job).select_related('candidate__user')

        # ステータスでフィルタリング
        status_filter = request.query_params.get('status', None)
        if status_filter:
            applications = applications.filter(status=status_filter)

        # マッチングスコアでソート
        applications = applications.order_by('-matching_score', '-applied_date')

        data = [{
            'id': app.id,
            'candidate_name': f"{app.candidate.user.first_name} {app.candidate.user.last_name}",
            'candidate_email': app.candidate.user.email,
            'applied_date': app.applied_date,
            'status': app.status,
            'matching_score': app.matching_score,
            'cover_letter': app.cover_letter[:200] if app.cover_letter else ''
        } for app in applications]

        return Response(data)

    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def matching_candidates(self, request, pk=None):
        """求人にマッチする候補者を取得"""
        job = self.get_object()

        # Only recruiters and admins can view
        if request.user.role not in ['recruiter', 'admin']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        # アクティブな候補者を取得
        candidates = Candidate.objects.filter(status='active')

        # マッチング結果を生成
        matching_results = []
        for candidate in candidates:
            # 既に応募済みの候補者はスキップ
            if Application.objects.filter(candidate=candidate, job=job).exists():
                continue

            score = self.calculate_matching_score(candidate, job)
            if score >= 50:  # 50点以上の候補者のみ表示
                matching_results.append({
                    'candidate_id': candidate.id,
                    'candidate_name': f"{candidate.user.first_name} {candidate.user.last_name}",
                    'candidate_email': candidate.user.email,
                    'current_position': candidate.current_position,
                    'years_of_experience': candidate.years_of_experience,
                    'matching_score': score,
                    'skills': [cs.skill.name for cs in candidate.candidate_skills.all()[:5]]
                })

        # スコアでソート
        matching_results.sort(key=lambda x: x['matching_score'], reverse=True)

        return Response(matching_results[:20])  # 上位20件を返す

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def generate_interview_questions(self, request, pk=None):
        """
        AgentCoreを使用して面接質問を生成
        """
        job = self.get_object()

        # Only recruiters and interviewers can generate questions
        if request.user.role not in ['recruiter', 'interviewer', 'admin']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            interview_type = request.data.get('interview_type', 'general')
            difficulty = request.data.get('difficulty', 'medium')
            count = request.data.get('count', 5)

            interviewer_copilot = InterviewerCopilotService()
            result = interviewer_copilot.generate_interview_questions(
                user_id=str(request.user.id),
                job_role=job.title,
                interview_type=interview_type,
                difficulty=difficulty,
                count=count
            )

            if result.get('success'):
                return Response({
                    'message': 'Interview questions generated successfully',
                    'questions': result.get('response'),
                    'session_id': result.get('session_id'),
                    'is_mock': result.get('is_mock', False)
                })
            else:
                return Response(
                    {'error': result.get('error', 'Failed to generate interview questions')},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        except Exception as e:
            logger.error(f"Interview questions generation error: {e}")
            return Response(
                {'error': f'An error occurred: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class JobSkillViewSet(viewsets.ModelViewSet):
    """求人スキル要件ビューセット"""
    queryset = JobSkill.objects.all()
    serializer_class = JobSkillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        return queryset.select_related('job', 'skill')


class JobRequirementViewSet(viewsets.ModelViewSet):
    """求人要件ビューセット"""
    queryset = JobRequirement.objects.all()
    serializer_class = JobRequirementSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        job_id = self.request.query_params.get('job', None)
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        requirement_type = self.request.query_params.get('type', None)
        if requirement_type:
            queryset = queryset.filter(requirement_type=requirement_type)

        return queryset.select_related('job').order_by('priority')


class MatchingResultViewSet(viewsets.ModelViewSet):
    """マッチング結果ビューセット"""
    queryset = MatchingResult.objects.all()
    serializer_class = MatchingResultSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        # 候補者は自分のマッチング結果のみ
        if user.role == 'candidate':
            try:
                candidate = user.candidate
                queryset = queryset.filter(candidate=candidate)
            except Candidate.DoesNotExist:
                queryset = queryset.none()

        # 採用担当者は自分が担当する求人のマッチング結果のみ
        elif user.role == 'recruiter':
            queryset = queryset.filter(job__hiring_manager=user)

        # フィルタリング
        min_score = self.request.query_params.get('min_score', None)
        if min_score:
            queryset = queryset.filter(matching_score__gte=min_score)

        is_applied = self.request.query_params.get('is_applied', None)
        if is_applied is not None:
            queryset = queryset.filter(is_applied=is_applied.lower() == 'true')

        return queryset.select_related('candidate__user', 'job').order_by('-matching_score')