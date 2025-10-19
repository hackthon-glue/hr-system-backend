from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """カスタムユーザーマネージャー"""

    def create_user(self, email, password=None, **extra_fields):
        """通常ユーザーを作成"""
        if not email:
            raise ValueError('メールアドレスは必須です')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """スーパーユーザーを作成"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('スーパーユーザーはis_staff=Trueである必要があります')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('スーパーユーザーはis_superuser=Trueである必要があります')

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """カスタムユーザーモデル"""

    ROLE_CHOICES = (
        ('candidate', '候補者'),
        ('recruiter', '採用担当者'),
        ('interviewer', '面接官'),
        ('admin', '管理者'),
    )

    email = models.EmailField('メールアドレス', unique=True)
    first_name = models.CharField('名', max_length=30, blank=True)
    last_name = models.CharField('姓', max_length=30, blank=True)
    first_name_kana = models.CharField('名（カナ）', max_length=30, blank=True)
    last_name_kana = models.CharField('姓（カナ）', max_length=30, blank=True)
    role = models.CharField('役割', max_length=20, choices=ROLE_CHOICES, default='candidate')
    phone = models.CharField('電話番号', max_length=20, blank=True)
    avatar = models.ImageField('アバター', upload_to='avatars/', blank=True, null=True)

    is_active = models.BooleanField('有効', default=True)
    is_staff = models.BooleanField('スタッフ', default=False)
    is_verified = models.BooleanField('メール認証済み', default=False)

    date_joined = models.DateTimeField('登録日時', default=timezone.now)
    last_login = models.DateTimeField('最終ログイン', blank=True, null=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    # Cognito関連フィールド
    cognito_user_id = models.CharField('Cognito User ID', max_length=100, blank=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'users'
        verbose_name = 'ユーザー'
        verbose_name_plural = 'ユーザー'

    def __str__(self):
        return self.email

    def get_full_name(self):
        """フルネームを取得"""
        return f"{self.last_name} {self.first_name}".strip() or self.email

    def get_short_name(self):
        """短縮名を取得"""
        return self.first_name or self.email
