"""
求人関連のカスタム権限クラス
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    オーナーのみ編集可能、それ以外は読み取りのみ
    """
    def has_permission(self, request, view):
        # 読み取り操作は誰でも可能
        if request.method in permissions.SAFE_METHODS:
            return True
        # 書き込み操作は認証済みユーザーのみ
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # 読み取り操作は誰でも可能
        if request.method in permissions.SAFE_METHODS:
            return True
        # オーナー（採用担当者）のみ編集可能
        return obj.hiring_manager == request.user


class IsAuthenticatedForWrite(permissions.BasePermission):
    """
    読み取りは誰でも可能、書き込みは認証必須
    """
    def has_permission(self, request, view):
        # GETリクエスト（一覧・詳細）は誰でも可能
        if request.method in permissions.SAFE_METHODS:
            return True
        # POST, PUT, PATCH, DELETE は認証必須
        return request.user and request.user.is_authenticated


class IsRecruiterOrReadOnly(permissions.BasePermission):
    """
    採用担当者のみ編集可能、それ以外は読み取りのみ
    """
    def has_permission(self, request, view):
        # 読み取り操作は誰でも可能
        if request.method in permissions.SAFE_METHODS:
            return True
        # 書き込み操作は採用担当者のみ
        return request.user and request.user.is_authenticated and \
               hasattr(request.user, 'role') and request.user.role in ['recruiter', 'admin']