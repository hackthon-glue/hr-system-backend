from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


class AuditLog(models.Model):
    """監査ログ"""

    ACTION_TYPE_CHOICES = (
        ('create', '作成'),
        ('read', '閲覧'),
        ('update', '更新'),
        ('delete', '削除'),
        ('login', 'ログイン'),
        ('logout', 'ログアウト'),
        ('export', 'エクスポート'),
        ('import', 'インポート'),
        ('approve', '承認'),
        ('reject', '却下'),
        ('send', '送信'),
        ('download', 'ダウンロード'),
    )

    SEVERITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '重大'),
    )

    # ユーザー情報
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='audit_logs',
        verbose_name='ユーザー',
        null=True,
        blank=True
    )
    user_email = models.EmailField('ユーザーメール', blank=True)
    user_role = models.CharField('ユーザー役割', max_length=50, blank=True)

    # アクション情報
    action_type = models.CharField('アクションタイプ', max_length=20, choices=ACTION_TYPE_CHOICES)
    resource_type = models.CharField('リソースタイプ', max_length=100)
    resource_id = models.CharField('リソースID', max_length=100, blank=True)
    description = models.TextField('説明')

    # 汎用外部キー（任意のモデルを参照可能）
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # 変更内容
    changes = models.JSONField('変更内容', default=dict, blank=True)
    old_values = models.JSONField('変更前の値', default=dict, blank=True)
    new_values = models.JSONField('変更後の値', default=dict, blank=True)

    # リクエスト情報
    ip_address = models.GenericIPAddressField('IPアドレス', null=True, blank=True)
    user_agent = models.TextField('ユーザーエージェント', blank=True)
    request_method = models.CharField('リクエストメソッド', max_length=10, blank=True)
    request_path = models.CharField('リクエストパス', max_length=500, blank=True)
    request_params = models.JSONField('リクエストパラメータ', default=dict, blank=True)

    # レスポンス情報
    status_code = models.IntegerField('ステータスコード', null=True, blank=True)
    response_time_ms = models.IntegerField('レスポンス時間（ミリ秒）', default=0)

    # メタ情報
    severity = models.CharField('重要度', max_length=20, choices=SEVERITY_CHOICES, default='low')
    is_suspicious = models.BooleanField('不審なアクティビティ', default=False)
    is_success = models.BooleanField('成功', default=True)
    error_message = models.TextField('エラーメッセージ', blank=True)

    # 追加メタデータ
    metadata = models.JSONField('メタデータ', default=dict, blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'audit_logs'
        verbose_name = '監査ログ'
        verbose_name_plural = '監査ログ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['action_type', '-created_at']),
            models.Index(fields=['resource_type', 'resource_id']),
            models.Index(fields=['ip_address', '-created_at']),
            models.Index(fields=['is_suspicious', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user_email or 'Anonymous'
        return f"{user_str} - {self.get_action_type_display()} {self.resource_type} at {self.created_at}"


class BiasReport(models.Model):
    """バイアスレポート"""

    BIAS_TYPE_CHOICES = (
        ('gender', '性別バイアス'),
        ('age', '年齢バイアス'),
        ('nationality', '国籍バイアス'),
        ('education', '学歴バイアス'),
        ('location', '地域バイアス'),
        ('name', '名前バイアス'),
        ('experience', '経験年数バイアス'),
        ('other', 'その他'),
    )

    SEVERITY_CHOICES = (
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('critical', '重大'),
    )

    STATUS_CHOICES = (
        ('pending', '未対応'),
        ('reviewing', '確認中'),
        ('addressed', '対応済み'),
        ('dismissed', '却下'),
        ('false_positive', '誤検知'),
    )

    # 検出情報
    bias_type = models.CharField('バイアスタイプ', max_length=30, choices=BIAS_TYPE_CHOICES)
    severity = models.CharField('重要度', max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending')

    # 対象情報
    target_type = models.CharField('対象タイプ', max_length=100)
    target_id = models.CharField('対象ID', max_length=100, blank=True)

    # 汎用外部キー
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # 詳細情報
    description = models.TextField('説明')
    evidence = models.JSONField('証拠データ', default=dict)
    detection_method = models.CharField('検出方法', max_length=100, blank=True)
    confidence_score = models.DecimalField(
        '信頼度スコア',
        max_digits=5,
        decimal_places=2,
        help_text='0-100の範囲'
    )

    # AI分析結果
    ai_analysis = models.TextField('AI分析', blank=True)
    suggested_actions = models.TextField('推奨アクション', blank=True)

    # 関連エンティティ
    related_job = models.ForeignKey(
        'jobs.Job',
        on_delete=models.SET_NULL,
        related_name='bias_reports',
        verbose_name='関連求人',
        null=True,
        blank=True
    )
    related_candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.SET_NULL,
        related_name='bias_reports',
        verbose_name='関連候補者',
        null=True,
        blank=True
    )
    related_application = models.ForeignKey(
        'candidates.Application',
        on_delete=models.SET_NULL,
        related_name='bias_reports',
        verbose_name='関連応募',
        null=True,
        blank=True
    )

    # 対応者情報
    detected_by_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='detected_bias_reports',
        verbose_name='検出ユーザー',
        null=True,
        blank=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_bias_reports',
        verbose_name='レビュー担当者',
        null=True,
        blank=True
    )
    review_notes = models.TextField('レビューメモ', blank=True)
    reviewed_at = models.DateTimeField('レビュー日時', null=True, blank=True)

    # 対応履歴
    action_taken = models.TextField('実施した対応', blank=True)
    action_taken_at = models.DateTimeField('対応日時', null=True, blank=True)

    # メタデータ
    metadata = models.JSONField('メタデータ', default=dict, blank=True)
    is_automated_detection = models.BooleanField('自動検出', default=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'bias_reports'
        verbose_name = 'バイアスレポート'
        verbose_name_plural = 'バイアスレポート'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['bias_type', '-created_at']),
            models.Index(fields=['severity', 'status']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['-confidence_score']),
        ]

    def __str__(self):
        return f"{self.get_bias_type_display()} - {self.get_severity_display()} ({self.get_status_display()})"

    def mark_as_reviewed(self, user, notes=''):
        """レビュー済みとしてマーク"""
        self.status = 'reviewing'
        self.reviewed_by = user
        self.review_notes = notes
        self.reviewed_at = timezone.now()
        self.save()

    def mark_as_addressed(self, user, action_description):
        """対応済みとしてマーク"""
        self.status = 'addressed'
        self.reviewed_by = user
        self.action_taken = action_description
        self.action_taken_at = timezone.now()
        self.save()


class DataAccessLog(models.Model):
    """個人情報アクセスログ"""

    ACCESS_TYPE_CHOICES = (
        ('view', '閲覧'),
        ('export', 'エクスポート'),
        ('download', 'ダウンロード'),
        ('print', '印刷'),
        ('share', '共有'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='data_access_logs',
        verbose_name='アクセスユーザー',
        null=True
    )

    # アクセス対象
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='accessed_data_logs',
        verbose_name='対象ユーザー',
        null=True
    )
    target_candidate = models.ForeignKey(
        'candidates.Candidate',
        on_delete=models.SET_NULL,
        related_name='data_access_logs',
        verbose_name='対象候補者',
        null=True,
        blank=True
    )

    # アクセス情報
    access_type = models.CharField('アクセスタイプ', max_length=20, choices=ACCESS_TYPE_CHOICES)
    accessed_fields = models.JSONField('アクセスフィールド', default=list)
    purpose = models.TextField('アクセス目的', blank=True)

    # リクエスト情報
    ip_address = models.GenericIPAddressField('IPアドレス', null=True, blank=True)
    user_agent = models.TextField('ユーザーエージェント', blank=True)

    # コンプライアンス
    is_authorized = models.BooleanField('認可済み', default=True)
    authorization_reason = models.TextField('認可理由', blank=True)
    is_gdpr_compliant = models.BooleanField('GDPR準拠', default=True)

    # メタデータ
    metadata = models.JSONField('メタデータ', default=dict, blank=True)

    created_at = models.DateTimeField('アクセス日時', auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'data_access_logs'
        verbose_name = '個人情報アクセスログ'
        verbose_name_plural = '個人情報アクセスログ'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['target_user', '-created_at']),
            models.Index(fields=['access_type', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.email if self.user else 'Unknown'} accessed {self.target_user.email if self.target_user else 'Unknown'}"


class ComplianceCheck(models.Model):
    """コンプライアンスチェック"""

    CHECK_TYPE_CHOICES = (
        ('gdpr', 'GDPR'),
        ('equal_opportunity', '機会均等'),
        ('data_retention', 'データ保持'),
        ('consent', '同意'),
        ('transparency', '透明性'),
        ('bias_detection', 'バイアス検出'),
        ('privacy', 'プライバシー'),
    )

    STATUS_CHOICES = (
        ('pending', '未実施'),
        ('in_progress', '実施中'),
        ('passed', '合格'),
        ('failed', '不合格'),
        ('warning', '警告'),
    )

    check_type = models.CharField('チェックタイプ', max_length=30, choices=CHECK_TYPE_CHOICES)
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending')

    # チェック対象
    target_type = models.CharField('対象タイプ', max_length=100)
    target_id = models.CharField('対象ID', max_length=100, blank=True)

    # 汎用外部キー
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    # チェック結果
    result_summary = models.TextField('結果サマリー')
    findings = models.JSONField('発見事項', default=list)
    recommendations = models.TextField('推奨事項', blank=True)
    compliance_score = models.DecimalField(
        'コンプライアンススコア',
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # 実施者情報
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='compliance_checks',
        verbose_name='チェック実施者',
        null=True,
        blank=True
    )
    checked_at = models.DateTimeField('チェック日時', null=True, blank=True)

    # 是正措置
    corrective_actions = models.TextField('是正措置', blank=True)
    corrective_actions_completed = models.BooleanField('是正完了', default=False)
    corrective_actions_completed_at = models.DateTimeField('是正完了日時', null=True, blank=True)

    # メタデータ
    metadata = models.JSONField('メタデータ', default=dict, blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        db_table = 'compliance_checks'
        verbose_name = 'コンプライアンスチェック'
        verbose_name_plural = 'コンプライアンスチェック'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['check_type', 'status']),
            models.Index(fields=['target_type', 'target_id']),
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.get_check_type_display()} - {self.get_status_display()}"


class SystemMetrics(models.Model):
    """システムメトリクス"""

    METRIC_TYPE_CHOICES = (
        ('api_call', 'API呼び出し'),
        ('agent_session', 'エージェントセッション'),
        ('matching', 'マッチング'),
        ('application', '応募'),
        ('user_action', 'ユーザーアクション'),
        ('error', 'エラー'),
        ('performance', 'パフォーマンス'),
    )

    metric_type = models.CharField('メトリクスタイプ', max_length=30, choices=METRIC_TYPE_CHOICES)
    metric_name = models.CharField('メトリクス名', max_length=100)
    metric_value = models.DecimalField('メトリクス値', max_digits=15, decimal_places=2)
    metric_unit = models.CharField('単位', max_length=50, blank=True)

    # ディメンション
    dimensions = models.JSONField('ディメンション', default=dict, blank=True)

    # 関連情報
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='system_metrics',
        verbose_name='ユーザー',
        null=True,
        blank=True
    )

    # タイムスタンプ
    timestamp = models.DateTimeField('タイムスタンプ', default=timezone.now, db_index=True)

    # メタデータ
    metadata = models.JSONField('メタデータ', default=dict, blank=True)

    created_at = models.DateTimeField('作成日時', auto_now_add=True)

    class Meta:
        db_table = 'system_metrics'
        verbose_name = 'システムメトリクス'
        verbose_name_plural = 'システムメトリクス'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['metric_type', '-timestamp']),
            models.Index(fields=['metric_name', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]

    def __str__(self):
        return f"{self.metric_name}: {self.metric_value} {self.metric_unit}"
