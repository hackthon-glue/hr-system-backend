from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Skill(models.Model):
    """スキルマスター"""

    CATEGORY_CHOICES = (
        ('programming', 'プログラミング'),
        ('framework', 'フレームワーク'),
        ('database', 'データベース'),
        ('cloud', 'クラウド'),
        ('tool', 'ツール'),
        ('soft_skill', 'ソフトスキル'),
        ('language', '言語'),
        ('other', 'その他'),
    )

    name = models.CharField('スキル名', max_length=100, unique=True)
    category = models.CharField('カテゴリ', max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField('説明', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'skills'
        verbose_name = 'スキル'
        verbose_name_plural = 'スキル'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class Candidate(models.Model):
    """候補者基本情報"""

    STATUS_CHOICES = (
        ('active', 'アクティブ'),
        ('inactive', '非アクティブ'),
        ('hired', '採用済み'),
        ('withdrawn', '辞退'),
    )

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='candidate',
        verbose_name='ユーザー'
    )

    # 基本情報
    date_of_birth = models.DateField('生年月日', blank=True, null=True)
    gender = models.CharField('性別', max_length=20, blank=True)
    nationality = models.CharField('国籍', max_length=50, blank=True)

    # 連絡先
    address = models.TextField('住所', blank=True)
    postal_code = models.CharField('郵便番号', max_length=10, blank=True)

    # 職務情報
    current_position = models.CharField('現職', max_length=200, blank=True)
    years_of_experience = models.IntegerField(
        '経験年数',
        default=0,
        validators=[MinValueValidator(0)]
    )

    # ステータス
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='active')
    available_date = models.DateField('入社可能日', blank=True, null=True)
    expected_salary = models.IntegerField('希望年収', blank=True, null=True)

    # ドキュメント
    resume = models.FileField('履歴書', upload_to='resumes/', blank=True, null=True)
    portfolio_url = models.URLField('ポートフォリオURL', blank=True)
    linkedin_url = models.URLField('LinkedIn URL', blank=True)
    github_url = models.URLField('GitHub URL', blank=True)

    # メタ情報
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'candidates'
        verbose_name = '候補者'
        verbose_name_plural = '候補者'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.current_position}"

    @property
    def age(self):
        """年齢を計算"""
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None


class CandidateProfile(models.Model):
    """候補者プロフィール詳細"""

    candidate = models.OneToOneField(
        Candidate,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='候補者'
    )

    # 自己紹介
    summary = models.TextField('自己紹介', blank=True)
    career_objective = models.TextField('キャリア目標', blank=True)

    # スキル評価
    technical_skills_summary = models.TextField('技術スキル概要', blank=True)
    soft_skills_summary = models.TextField('ソフトスキル概要', blank=True)

    # 希望条件
    preferred_work_style = models.CharField('希望勤務形態', max_length=50, blank=True)
    preferred_location = models.CharField('希望勤務地', max_length=200, blank=True)
    willing_to_relocate = models.BooleanField('転勤可能', default=False)
    remote_work_preference = models.CharField('リモートワーク希望', max_length=50, blank=True)

    # 言語能力
    japanese_level = models.CharField('日本語レベル', max_length=20, blank=True)
    english_level = models.CharField('英語レベル', max_length=20, blank=True)
    other_languages = models.TextField('その他言語', blank=True)

    # その他
    certifications = models.TextField('資格・認定', blank=True)
    awards = models.TextField('受賞歴', blank=True)
    publications = models.TextField('論文・執筆', blank=True)
    references = models.TextField('推薦者情報', blank=True)

    # AI分析結果
    ai_summary = models.TextField('AI分析サマリー', blank=True)
    strengths = models.TextField('強み', blank=True)
    improvement_areas = models.TextField('改善エリア', blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'candidate_profiles'
        verbose_name = '候補者プロフィール'
        verbose_name_plural = '候補者プロフィール'

    def __str__(self):
        return f"{self.candidate.user.get_full_name()}のプロフィール"


class CandidateSkill(models.Model):
    """候補者スキル"""

    PROFICIENCY_CHOICES = (
        ('beginner', '初級'),
        ('intermediate', '中級'),
        ('advanced', '上級'),
        ('expert', 'エキスパート'),
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='candidate_skills',
        verbose_name='候補者'
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name='candidate_skills',
        verbose_name='スキル'
    )
    proficiency_level = models.CharField('習熟度', max_length=20, choices=PROFICIENCY_CHOICES)
    years_of_experience = models.IntegerField(
        '経験年数',
        default=0,
        validators=[MinValueValidator(0)]
    )
    last_used_date = models.DateField('最終使用日', blank=True, null=True)
    is_primary = models.BooleanField('主要スキル', default=False)
    notes = models.TextField('備考', blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'candidate_skills'
        verbose_name = '候補者スキル'
        verbose_name_plural = '候補者スキル'
        unique_together = [['candidate', 'skill']]
        ordering = ['-is_primary', '-years_of_experience']

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.skill.name} ({self.get_proficiency_level_display()})"


class Education(models.Model):
    """学歴"""

    DEGREE_CHOICES = (
        ('high_school', '高校'),
        ('associate', '準学士'),
        ('bachelor', '学士'),
        ('master', '修士'),
        ('doctorate', '博士'),
        ('other', 'その他'),
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='educations',
        verbose_name='候補者'
    )

    institution_name = models.CharField('学校名', max_length=200)
    degree = models.CharField('学位', max_length=20, choices=DEGREE_CHOICES)
    field_of_study = models.CharField('専攻', max_length=200)
    start_date = models.DateField('開始日')
    end_date = models.DateField('終了日', blank=True, null=True)
    is_current = models.BooleanField('在学中', default=False)
    gpa = models.DecimalField(
        'GPA',
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    description = models.TextField('説明', blank=True)
    location = models.CharField('所在地', max_length=200, blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'educations'
        verbose_name = '学歴'
        verbose_name_plural = '学歴'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.institution_name} ({self.get_degree_display()})"


class WorkExperience(models.Model):
    """職歴"""

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='work_experiences',
        verbose_name='候補者'
    )

    company_name = models.CharField('会社名', max_length=200)
    position = models.CharField('役職', max_length=200)
    employment_type = models.CharField('雇用形態', max_length=50, blank=True)
    location = models.CharField('勤務地', max_length=200, blank=True)
    start_date = models.DateField('開始日')
    end_date = models.DateField('終了日', blank=True, null=True)
    is_current = models.BooleanField('現職', default=False)

    description = models.TextField('職務内容', blank=True)
    achievements = models.TextField('実績', blank=True)
    technologies_used = models.TextField('使用技術', blank=True)
    team_size = models.IntegerField(
        'チーム規模',
        blank=True,
        null=True,
        validators=[MinValueValidator(1)]
    )

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'work_experiences'
        verbose_name = '職歴'
        verbose_name_plural = '職歴'
        ordering = ['-start_date']

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} - {self.position} at {self.company_name}"

    @property
    def duration_months(self):
        """勤務期間（月数）を計算"""
        end = self.end_date or timezone.now().date()
        return (end.year - self.start_date.year) * 12 + (end.month - self.start_date.month)


class Application(models.Model):
    """応募情報"""

    STATUS_CHOICES = (
        ('draft', '下書き'),
        ('submitted', '応募済み'),
        ('screening', '書類選考中'),
        ('interview', '面接中'),
        ('offer', '内定'),
        ('accepted', '承諾'),
        ('rejected', '不合格'),
        ('withdrawn', '辞退'),
    )

    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='候補者'
    )
    job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.CASCADE,
        related_name='applications',
        verbose_name='求人'
    )

    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    applied_date = models.DateTimeField('応募日時', auto_now_add=True)

    # 応募書類
    cover_letter = models.TextField('志望動機', blank=True)
    resume_version = models.FileField('履歴書（応募時版）', upload_to='applications/resumes/', blank=True, null=True)

    # スコアリング
    matching_score = models.DecimalField(
        'マッチングスコア',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    ai_recommendation = models.TextField('AI推薦コメント', blank=True)

    # 選考情報
    screening_notes = models.TextField('選考メモ', blank=True)
    interview_count = models.IntegerField('面接回数', default=0)
    last_interview_date = models.DateTimeField('最終面接日', blank=True, null=True)

    # 内定情報
    offer_date = models.DateTimeField('内定日', blank=True, null=True)
    offer_salary = models.IntegerField('提示年収', blank=True, null=True)
    offer_notes = models.TextField('内定メモ', blank=True)

    # 担当者
    assigned_recruiter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_applications',
        verbose_name='担当リクルーター',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'applications'
        verbose_name = '応募'
        verbose_name_plural = '応募'
        unique_together = [['candidate', 'job']]
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} -> {self.job.title} ({self.get_status_display()})"

    @property
    def days_since_application(self):
        """応募からの経過日数"""
        return (timezone.now() - self.applied_date).days


class Interview(models.Model):
    """面接記録"""

    INTERVIEW_TYPE_CHOICES = (
        ('phone', '電話'),
        ('video', 'オンライン'),
        ('onsite', '対面'),
        ('technical', '技術面接'),
        ('hr', '人事面接'),
        ('final', '最終面接'),
    )

    RESULT_CHOICES = (
        ('pending', '未実施'),
        ('completed', '完了（評価待ち）'),
        ('passed', '合格'),
        ('failed', '不合格'),
        ('on_hold', '保留'),
    )

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name='interviews',
        verbose_name='応募'
    )

    interview_type = models.CharField('面接種類', max_length=20, choices=INTERVIEW_TYPE_CHOICES)
    round_number = models.IntegerField('面接回数', validators=[MinValueValidator(1)])
    scheduled_date = models.DateTimeField('予定日時')
    duration_minutes = models.IntegerField('所要時間（分）', default=60)

    # 面接官
    interviewers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='conducted_interviews',
        verbose_name='面接官'
    )

    # 評価
    result = models.CharField('結果', max_length=20, choices=RESULT_CHOICES, default='pending')
    technical_score = models.IntegerField(
        '技術評価',
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    communication_score = models.IntegerField(
        'コミュニケーション評価',
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    cultural_fit_score = models.IntegerField(
        'カルチャーフィット評価',
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    overall_score = models.IntegerField(
        '総合評価',
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )

    # フィードバック
    feedback = models.TextField('フィードバック', blank=True)
    strengths = models.TextField('強み', blank=True)
    weaknesses = models.TextField('弱み', blank=True)
    notes = models.TextField('メモ', blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'interviews'
        verbose_name = '面接'
        verbose_name_plural = '面接'
        ordering = ['application', 'round_number']

    def __str__(self):
        return f"{self.application.candidate.user.get_full_name()} - {self.get_interview_type_display()} (第{self.round_number}回)"
