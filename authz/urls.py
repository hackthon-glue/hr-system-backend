from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

app_name = 'authz'

urlpatterns = [
    # 認証
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ユーザー情報
    path('user/', views.get_current_user, name='get_current_user'),
    path('user/update/', views.update_user, name='update_user'),

    # パスワード管理
    path('change-password/', views.change_password, name='change_password'),
    path('password-reset/', views.request_password_reset, name='request_password_reset'),
]