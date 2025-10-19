from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Job, JobRequirement, JobSkill, MatchingResult, SavedJob, JobView
)
from candidates.models import Skill, Candidate

User = get_user_model()


class JobRequirementSerializer(serializers.ModelSerializer):
    """求人要件シリアライザー"""

    requirement_type_display = serializers.CharField(source='get_requirement_type_display', read_only=True)

    class Meta:
        model = JobRequirement
        fields = [
            'id', 'requirement_type', 'requirement_type_display',
            'category', 'description', 'priority',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class JobSkillSerializer(serializers.ModelSerializer):
    """求人スキルシリアライザー"""

    skill_name = serializers.CharField(source='skill.name', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    requirement_level_display = serializers.CharField(source='get_requirement_level_display', read_only=True)
    minimum_proficiency_display = serializers.CharField(source='get_minimum_proficiency_display', read_only=True)

    class Meta:
        model = JobSkill
        fields = [
            'id', 'skill', 'skill_name', 'skill_category',
            'requirement_level', 'requirement_level_display',
            'minimum_proficiency', 'minimum_proficiency_display',
            'minimum_years', 'weight', 'notes',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class JobListSerializer(serializers.ModelSerializer):
    """求人一覧シリアライザー"""

    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'job_code', 'department', 'location',
            'remote_work_option', 'employment_type', 'employment_type_display',
            'experience_level', 'experience_level_display',
            'salary_min', 'salary_max', 'status', 'status_display',
            'is_featured', 'deadline', 'view_count', 'application_count',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['job_code', 'view_count', 'application_count', 'created_at', 'updated_at', 'is_active']


class JobDetailSerializer(serializers.ModelSerializer):
    """求人詳細シリアライザー"""

    employment_type_display = serializers.CharField(source='get_employment_type_display', read_only=True)
    experience_level_display = serializers.CharField(source='get_experience_level_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    requirements = JobRequirementSerializer(many=True, read_only=True)
    job_skills = JobSkillSerializer(many=True, read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Job
        fields = [
            'id', 'title', 'job_code', 'department', 'location',
            'remote_work_option', 'employment_type', 'employment_type_display',
            'experience_level', 'experience_level_display',
            'description', 'responsibilities', 'qualifications',
            'preferred_qualifications', 'salary_min', 'salary_max',
            'salary_currency', 'benefits', 'number_of_positions',
            'deadline', 'start_date', 'status', 'status_display',
            'is_featured', 'priority', 'view_count', 'application_count',
            'requirements', 'job_skills', 'is_active',
            'published_date', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'job_code', 'view_count', 'application_count',
            'published_date', 'created_at', 'updated_at', 'is_active'
        ]


class JobCreateUpdateSerializer(serializers.ModelSerializer):
    """求人作成・更新シリアライザー"""

    requirements_data = JobRequirementSerializer(many=True, required=False, write_only=True)
    job_skills_data = JobSkillSerializer(many=True, required=False, write_only=True)

    class Meta:
        model = Job
        fields = [
            'title', 'department', 'location', 'remote_work_option',
            'employment_type', 'experience_level', 'description',
            'responsibilities', 'qualifications', 'preferred_qualifications',
            'salary_min', 'salary_max', 'salary_currency', 'benefits',
            'number_of_positions', 'deadline', 'start_date',
            'status', 'is_featured', 'priority',
            'requirements_data', 'job_skills_data'
        ]

    def create(self, validated_data):
        requirements_data = validated_data.pop('requirements_data', [])
        job_skills_data = validated_data.pop('job_skills_data', [])

        # 求人コードを自動生成
        import uuid
        validated_data['job_code'] = f"JOB-{uuid.uuid4().hex[:8].upper()}"

        # ユーザー設定
        user = self.context['request'].user
        validated_data['hiring_manager'] = user

        job = Job.objects.create(**validated_data)

        # 要件作成
        for req_data in requirements_data:
            JobRequirement.objects.create(job=job, **req_data)

        # スキル作成
        for skill_data in job_skills_data:
            JobSkill.objects.create(job=job, **skill_data)

        return job

    def update(self, instance, validated_data):
        requirements_data = validated_data.pop('requirements_data', None)
        job_skills_data = validated_data.pop('job_skills_data', None)

        # 基本情報更新
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 要件更新（既存削除して再作成）
        if requirements_data is not None:
            instance.requirements.all().delete()
            for req_data in requirements_data:
                JobRequirement.objects.create(job=instance, **req_data)

        # スキル更新（既存削除して再作成）
        if job_skills_data is not None:
            instance.job_skills.all().delete()
            for skill_data in job_skills_data:
                JobSkill.objects.create(job=instance, **skill_data)

        return instance


class MatchingResultSerializer(serializers.ModelSerializer):
    """マッチング結果シリアライザー"""

    job_title = serializers.CharField(source='job.title', read_only=True)
    candidate_name = serializers.CharField(source='candidate.user.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    recommendation_level_display = serializers.CharField(source='get_recommendation_level_display', read_only=True)

    class Meta:
        model = MatchingResult
        fields = [
            'id', 'job', 'job_title', 'candidate', 'candidate_name',
            'overall_score', 'skill_match_score', 'experience_match_score',
            'education_match_score', 'culture_fit_score',
            'matched_skills', 'missing_skills', 'extra_skills',
            'ai_summary', 'strengths', 'weaknesses', 'recommendation',
            'recommendation_level', 'recommendation_level_display',
            'status', 'status_display', 'calculation_method',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class MatchingResultCreateSerializer(serializers.ModelSerializer):
    """マッチング結果作成シリアライザー"""

    class Meta:
        model = MatchingResult
        fields = [
            'job', 'candidate', 'overall_score',
            'skill_match_score', 'experience_match_score',
            'education_match_score', 'culture_fit_score',
            'matched_skills', 'missing_skills', 'extra_skills',
            'ai_summary', 'strengths', 'weaknesses',
            'recommendation', 'recommendation_level',
            'calculation_method'
        ]

    def create(self, validated_data):
        validated_data['calculated_by'] = self.context['request'].user
        validated_data['status'] = 'completed'
        return super().create(validated_data)


class SavedJobSerializer(serializers.ModelSerializer):
    """保存済み求人シリアライザー"""

    job = JobListSerializer(read_only=True)
    job_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = SavedJob
        fields = [
            'id', 'job', 'job_id', 'notes', 'is_notified',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def create(self, validated_data):
        # 現在のユーザーの候補者情報を取得
        user = self.context['request'].user
        try:
            candidate = user.candidate
        except Candidate.DoesNotExist:
            raise serializers.ValidationError("候補者プロフィールが見つかりません。")

        job_id = validated_data.pop('job_id')
        try:
            job = Job.objects.get(id=job_id)
        except Job.DoesNotExist:
            raise serializers.ValidationError("求人が見つかりません。")

        validated_data['candidate'] = candidate
        validated_data['job'] = job

        return super().create(validated_data)


class JobViewSerializer(serializers.ModelSerializer):
    """求人閲覧履歴シリアライザー"""

    job_title = serializers.CharField(source='job.title', read_only=True)

    class Meta:
        model = JobView
        fields = [
            'id', 'job', 'job_title', 'ip_address',
            'user_agent', 'referrer', 'viewed_at'
        ]
        read_only_fields = ['viewed_at']
