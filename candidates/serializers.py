from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Skill, Candidate, CandidateProfile, CandidateSkill,
    Education, WorkExperience, Application, Interview
)
from jobs.models import Job

User = get_user_model()


class SkillSerializer(serializers.ModelSerializer):
    """スキルシリアライザー"""

    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = Skill
        fields = [
            'id', 'name', 'category', 'category_display',
            'description', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class CandidateSkillSerializer(serializers.ModelSerializer):
    """候補者スキルシリアライザー"""

    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    proficiency_level_display = serializers.CharField(source='get_proficiency_level_display', read_only=True)

    class Meta:
        model = CandidateSkill
        fields = [
            'id', 'skill', 'skill_name', 'skill_category',
            'proficiency_level', 'proficiency_level_display',
            'years_of_experience', 'last_used_date', 'is_primary',
            'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EducationSerializer(serializers.ModelSerializer):
    """学歴シリアライザー"""

    degree_display = serializers.CharField(source='get_degree_display', read_only=True)

    class Meta:
        model = Education
        fields = [
            'id', 'institution_name', 'degree', 'degree_display',
            'field_of_study', 'start_date', 'end_date', 'is_current',
            'gpa', 'description', 'location',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class WorkExperienceSerializer(serializers.ModelSerializer):
    """職歴シリアライザー"""

    duration_months = serializers.IntegerField(read_only=True)

    class Meta:
        model = WorkExperience
        fields = [
            'id', 'company_name', 'position', 'employment_type',
            'location', 'start_date', 'end_date', 'is_current',
            'description', 'achievements', 'technologies_used',
            'team_size', 'duration_months',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'duration_months']


class CandidateProfileSerializer(serializers.ModelSerializer):
    """候補者プロフィールシリアライザー"""

    class Meta:
        model = CandidateProfile
        fields = [
            'id', 'summary', 'career_objective',
            'technical_skills_summary', 'soft_skills_summary',
            'preferred_work_style', 'preferred_location',
            'willing_to_relocate', 'remote_work_preference',
            'japanese_level', 'english_level', 'other_languages',
            'certifications', 'awards', 'publications', 'references',
            'ai_summary', 'strengths', 'improvement_areas',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'ai_summary', 'strengths', 'improvement_areas']


class UserBasicSerializer(serializers.ModelSerializer):
    """ユーザー基本情報シリアライザー"""

    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'role']
        read_only_fields = ['id', 'email']


class CandidateListSerializer(serializers.ModelSerializer):
    """候補者一覧シリアライザー（簡易版）"""

    user = UserBasicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id', 'user', 'current_position', 'years_of_experience',
            'status', 'status_display', 'age', 'expected_salary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'age']


class CandidateDetailSerializer(serializers.ModelSerializer):
    """候補者詳細シリアライザー"""

    user = UserBasicSerializer(read_only=True)
    profile = CandidateProfileSerializer(read_only=True)
    candidate_skills = CandidateSkillSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    work_experiences = WorkExperienceSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    age = serializers.IntegerField(read_only=True)

    class Meta:
        model = Candidate
        fields = [
            'id', 'user', 'date_of_birth', 'gender', 'nationality',
            'address', 'postal_code', 'current_position',
            'years_of_experience', 'status', 'status_display',
            'available_date', 'expected_salary', 'age',
            'resume', 'portfolio_url', 'linkedin_url', 'github_url',
            'profile', 'candidate_skills', 'educations', 'work_experiences',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'age']


class CandidateCreateUpdateSerializer(serializers.ModelSerializer):
    """候補者作成・更新シリアライザー"""

    class Meta:
        model = Candidate
        fields = [
            'date_of_birth', 'gender', 'nationality',
            'address', 'postal_code', 'current_position',
            'years_of_experience', 'status',
            'available_date', 'expected_salary',
            'resume', 'portfolio_url', 'linkedin_url', 'github_url'
        ]


class JobBasicSerializer(serializers.ModelSerializer):
    """求人基本情報シリアライザー"""

    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'job_code', 'department', 'location',
            'employment_type', 'employment_type_display',
            'experience_level', 'experience_level_display',
            'salary_min', 'salary_max', 'status'
        ]
        read_only_fields = ['id', 'job_code']


class ApplicationListSerializer(serializers.ModelSerializer):
    """応募一覧シリアライザー"""

    candidate_name = serializers.CharField(source='candidate.user.get_full_name', read_only=True)
    job = JobBasicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_since_application = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'candidate', 'candidate_name', 'job',
            'status', 'status_display', 'applied_date',
            'matching_score', 'interview_count',
            'days_since_application', 'created_at', 'updated_at'
        ]
        read_only_fields = ['applied_date', 'created_at', 'updated_at', 'days_since_application']


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """応募詳細シリアライザー"""

    candidate = CandidateListSerializer(read_only=True)
    job = JobBasicSerializer(read_only=True)
    assigned_recruiter = UserBasicSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    days_since_application = serializers.IntegerField(read_only=True)

    class Meta:
        model = Application
        fields = [
            'id', 'candidate', 'job', 'status', 'status_display',
            'applied_date', 'cover_letter', 'resume_version',
            'matching_score', 'ai_recommendation',
            'screening_notes', 'interview_count', 'last_interview_date',
            'offer_date', 'offer_salary', 'offer_notes',
            'assigned_recruiter', 'days_since_application',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['applied_date', 'created_at', 'updated_at', 'days_since_application']


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """応募作成シリアライザー"""

    class Meta:
        model = Application
        fields = ['job', 'cover_letter', 'resume_version']

    def create(self, validated_data):
        # 現在のユーザーの候補者情報を取得
        user = self.context['request'].user
        try:
            candidate = user.candidate
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("候補者プロフィールが見つかりません。")

        validated_data['candidate'] = candidate
        return super().create(validated_data)


class InterviewSerializer(serializers.ModelSerializer):
    """面接シリアライザー"""

    application_info = ApplicationListSerializer(source='application', read_only=True)
    interviewers = UserBasicSerializer(many=True, read_only=True)
    interview_type_display = serializers.CharField(source='get_interview_type_display', read_only=True)
    result_display = serializers.CharField(source='get_result_display', read_only=True)
    candidate_answers = serializers.SerializerMethodField()

    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'application_info',
            'interview_type', 'interview_type_display',
            'round_number', 'scheduled_date', 'duration_minutes',
            'interviewers', 'result', 'result_display',
            'technical_score', 'communication_score',
            'cultural_fit_score', 'overall_score',
            'feedback', 'strengths', 'weaknesses', 'notes',
            'candidate_answers',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def get_candidate_answers(self, obj):
        """notesフィールドからJSONパースした回答データを返す"""
        import json
        if obj.notes:
            try:
                return json.loads(obj.notes)
            except (json.JSONDecodeError, TypeError):
                # JSONでない場合はそのまま返す
                return {'raw_notes': obj.notes}
        return None


class InterviewCreateUpdateSerializer(serializers.ModelSerializer):
    """面接作成・更新シリアライザー"""

    interviewer_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )

    class Meta:
        model = Interview
        fields = [
            'application', 'interview_type', 'round_number',
            'scheduled_date', 'duration_minutes', 'interviewer_ids',
            'result', 'technical_score', 'communication_score',
            'cultural_fit_score', 'overall_score',
            'feedback', 'strengths', 'weaknesses', 'notes'
        ]

    def create(self, validated_data):
        interviewer_ids = validated_data.pop('interviewer_ids', [])
        interview = super().create(validated_data)

        if interviewer_ids:
            interviewers = User.objects.filter(id__in=interviewer_ids)
            interview.interviewers.set(interviewers)

        return interview

    def update(self, instance, validated_data):
        interviewer_ids = validated_data.pop('interviewer_ids', None)
        interview = super().update(instance, validated_data)

        if interviewer_ids is not None:
            interviewers = User.objects.filter(id__in=interviewer_ids)
            interview.interviewers.set(interviewers)

        return interview
