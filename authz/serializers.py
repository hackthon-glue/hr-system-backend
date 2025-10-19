from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """ユーザー基本情報シリアライザー"""
    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name',
            'first_name_kana', 'last_name_kana', 'role',
            'phone', 'is_verified', 'date_joined'
        )
        read_only_fields = ('id', 'is_verified', 'date_joined')


class RegisterSerializer(serializers.ModelSerializer):
    """ユーザー登録用シリアライザー"""
    password = serializers.CharField(write_only=True, min_length=6)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'first_name_kana',
            'last_name_kana', 'role', 'phone'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("パスワードが一致しません")
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    """ログイン用シリアライザー"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(email=email, password=password)

            if not user:
                raise serializers.ValidationError('メールアドレスまたはパスワードが正しくありません')

            if not user.is_active:
                raise serializers.ValidationError('このアカウントは無効化されています')

        else:
            raise serializers.ValidationError('メールアドレスとパスワードを入力してください')

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    """パスワード変更用シリアライザー"""
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)
    new_password_confirm = serializers.CharField(write_only=True)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('現在のパスワードが正しくありません')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError('新しいパスワードが一致しません')
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user