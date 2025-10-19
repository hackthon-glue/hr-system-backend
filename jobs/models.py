from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Job(models.Model):
    """求人情報"""

    STATUS_CHOICES = (
        ('draft', '下書き'),
        ('active', '公開中'),
        ('paused', '一時停止'),
        ('closed', '募集終了'),
        ('filled', '採用完了'),
    )

    EMPLOYMENT_TYPE_CHOICES = (
        ('full_time', '正社員'),
        ('contract', '契約社員'),
        ('part_time', 'パートタイム'),
        ('internship', 'インターン'),
        ('temporary', '派遣'),
    )

    EXPERIENCE_LEVEL_CHOICES = (
        ('entry', '新卒・未経験'),
        ('junior', 'ジュニア（1-3年）'),
        ('mid', 'ミドル（3-7年）'),
        ('senior', 'シニア（7年以上）'),
        ('lead', 'リード・マネージャー'),
    )

    # 基本情報
    title = models.CharField('求人タイトル', max_length=200)
    job_code = models.CharField('求人コード', max_length=50, unique=True)
    department = models.CharField('部署', max_length=100)
    location = models.CharField('勤務地', max_length=200)
    remote_work_option = models.CharField('リモートワーク', max_length=50, blank=True)

    # 雇用形態
    employment_type = models.CharField(
        '雇用形態',
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES
    )
    experience_level = models.CharField(
        '経験レベル',
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES
    )

    # 職務内容
    description = models.TextField('職務内容')
    responsibilities = models.TextField('主な責任')
    qualifications = models.TextField('応募資格')
    preferred_qualifications = models.TextField('歓迎要件', blank=True)

    # 待遇
    salary_min = models.IntegerField(
        '最低年収',
        validators=[MinValueValidator(0)]
    )
    salary_max = models.IntegerField(
        '最高年収',
        validators=[MinValueValidator(0)]
    )
    salary_currency = models.CharField('通貨', max_length=3, default='JPY')
    benefits = models.TextField('福利厚生', blank=True)

    # 募集情報
    number_of_positions = models.IntegerField(
        '募集人数',
        default=1,
        validators=[MinValueValidator(1)]
    )
    deadline = models.DateField('応募締切', blank=True, null=True)
    start_date = models.DateField('勤務開始日', blank=True, null=True)

    # ステータス
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField('注目求人', default=False)
    priority = models.IntegerField(
        '優先度',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    # 担当者
    hiring_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='managed_jobs',
        verbose_name='採用マネージャー',
        null=True
    )
    recruiters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='recruiting_jobs',
        verbose_name='担当リクルーター',
        blank=True
    )

    # メタ情報
    view_count = models.IntegerField('閲覧数', default=0)
    application_count = models.IntegerField('応募数', default=0)
    published_date = models.DateTimeField('公開日時', blank=True, null=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'jobs'
        verbose_name = '求人'
        verbose_name_plural = '求人'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'employment_type']),
            models.Index(fields=['job_code']),
        ]

    def __str__(self):
        return f"{self.job_code} - {self.title}"

    def save(self, *args, **kwargs):
        """公開日時を自動設定"""
        if self.status == 'active' and not self.published_date:
            self.published_date = timezone.now()
        super().save(*args, **kwargs)

    @property
    def is_active(self):
        """求人が有効かどうか"""
        if self.status != 'active':
            return False
        if self.deadline and self.deadline < timezone.now().date():
            return False
        return True


class JobRequirement(models.Model):
    """求人要件"""

    REQUIREMENT_TYPE_CHOICES = (
        ('required', '必須'),
        ('preferred', '歓迎'),
        ('nice_to_have', 'あれば尚可'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name='求人'
    )

    requirement_type = models.CharField(
        '要件タイプ',
        max_length=20,
        choices=REQUIREMENT_TYPE_CHOICES
    )
    category = models.CharField('カテゴリ', max_length=50)
    description = models.TextField('説明')
    priority = models.IntegerField(
        '優先度',
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'job_requirements'
        verbose_name = '求人要件'
        verbose_name_plural = '求人要件'
        ordering = ['job', '-priority']

    def __str__(self):
        return f"{self.job.title} - {self.category} ({self.get_requirement_type_display()})"


class JobSkill(models.Model):
    """求人に必要なスキル"""

    REQUIREMENT_LEVEL_CHOICES = (
        ('required', '必須'),
        ('preferred', '歓迎'),
    )

    PROFICIENCY_LEVEL_CHOICES = (
        ('beginner', '初級'),
        ('intermediate', '中級'),
        ('advanced', '上級'),
        ('expert', 'エキスパート'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='job_skills',
        verbose_name='求人'
    )
    skill = models.ForeignKey(
        'candidates.Skill',
        on_delete=models.CASCADE,
        related_name='job_skills',
        verbose_name='スキル'
    )

    requirement_level = models.CharField(
        '要求レベル',
        max_length=20,
        choices=REQUIREMENT_LEVEL_CHOICES
    )
    minimum_proficiency = models.CharField(
        '最低習熟度',
        max_length=20,
        choices=PROFICIENCY_LEVEL_CHOICES
    )
    minimum_years = models.IntegerField(
        '最低経験年数',
        default=0,
        validators=[MinValueValidator(0)]
    )
    weight = models.IntegerField(
        '重み',
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text='マッチングスコア計算時の重み付け'
    )
    notes = models.TextField('備考', blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'job_skills'
        verbose_name = '求人スキル'
        verbose_name_plural = '求人スキル'
        unique_together = [['job', 'skill']]
        ordering = ['-requirement_level', '-weight']

    def __str__(self):
        return f"{self.job.title} - {self.skill.name} ({self.get_requirement_level_display()})"


class MatchingResult(models.Model):
    """マッチング結果"""

    STATUS_CHOICES = (
        ('pending', '処理中'),
        ('completed', '完了'),
        ('failed', '失敗'),
    )

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='matching_results',
        verbose_name='求人'
    )
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='matching_results',
        verbose_name='候補者'
    )

    # スコアリング
    overall_score = models.DecimalField(
        '総合スコア',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    skill_match_score = models.DecimalField(
        'スキルマッチスコア',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    experience_match_score = models.DecimalField(
        '経験マッチスコア',
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    education_match_score = models.DecimalField(
        '学歴マッチスコア',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    culture_fit_score = models.DecimalField(
        'カルチャーフィットスコア',
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    # マッチング詳細
    matched_skills = models.JSONField('マッチしたスキル', default=list)
    missing_skills = models.JSONField('不足スキル', default=list)
    extra_skills = models.JSONField('追加スキル', default=list)

    # AI分析
    ai_summary = models.TextField('AI分析サマリー', blank=True)
    strengths = models.TextField('強み', blank=True)
    weaknesses = models.TextField('弱み', blank=True)
    recommendation = models.TextField('推薦コメント', blank=True)
    recommendation_level = models.CharField(
        '推薦レベル',
        max_length=20,
        choices=(
            ('highly_recommended', '強く推薦'),
            ('recommended', '推薦'),
            ('consider', '検討可'),
            ('not_recommended', '非推薦'),
        ),
        blank=True
    )

    # メタ情報
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending')
    calculated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='calculated_matchings',
        verbose_name='計算実行者',
        null=True,
        blank=True
    )
    calculation_method = models.CharField('計算方法', max_length=100, blank=True)
    error_message = models.TextField('エラーメッセージ', blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'matching_results'
        verbose_name = 'マッチング結果'
        verbose_name_plural = 'マッチング結果'
        unique_together = [['job', 'candidate']]
        ordering = ['-overall_score', '-created_at']
        indexes = [
            models.Index(fields=['job', '-overall_score']),
            models.Index(fields=['candidate', '-overall_score']),
        ]

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} x {self.job.title} - {self.overall_score}%"


class SavedJob(models.Model):
    """保存した求人"""

    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='saved_jobs',
        verbose_name='候補者'
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='saved_by',
        verbose_name='求人'
    )

    notes = models.TextField('メモ', blank=True)
    is_notified = models.BooleanField('通知済み', default=False)

    created_at = models.DateTimeField('保存日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'saved_jobs'
        verbose_name = '保存済み求人'
        verbose_name_plural = '保存済み求人'
        unique_together = [['candidate', 'job']]
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.candidate.user.get_full_name()} saved {self.job.title}"


class JobView(models.Model):
    """求人閲覧履歴"""

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name='views',
        verbose_name='求人'
    )
    candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.CASCADE,
        related_name='job_views',
        verbose_name='候補者',
        blank=True,
        null=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='job_views',
        verbose_name='ユーザー',
        blank=True,
        null=True
    )

    ip_address = models.GenericIPAddressField('IPアドレス', blank=True, null=True)
    user_agent = models.TextField('ユーザーエージェント', blank=True)
    referrer = models.URLField('参照元', blank=True)

    viewed_at = models.DateTimeField('閲覧日時', auto_now_add=True)

    class Meta:
        db_table = 'job_views'
        verbose_name = '求人閲覧履歴'
        verbose_name_plural = '求人閲覧履歴'
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['job', '-viewed_at']),
            models.Index(fields=['candidate', '-viewed_at']),
        ]

    def __str__(self):
        viewer = self.candidate.user.get_full_name() if self.candidate else 'Anonymous'
        return f"{viewer} viewed {self.job.title}"
