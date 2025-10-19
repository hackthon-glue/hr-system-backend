"""
監査ログミドルウェア
全てのリクエストとレスポンスを記録し、監査証跡を作成します。
"""

import json
import time
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.contenttypes.models import ContentType
from .models import AuditLog, DataAccessLog


class AuditLogMiddleware(MiddlewareMixin):
    """
    監査ログミドルウェア
    全てのHTTPリクエストを記録し、監査証跡を作成します。
    """

    # ログ対象外のパス
    EXCLUDED_PATHS = [
        '/admin/jsi18n/',
        '/static/',
        '/media/',
        '/favicon.ico',
    ]

    # ログ対象外のメソッド
    EXCLUDED_METHODS = ['OPTIONS']

    def process_request(self, request):
        """リクエスト処理開始時"""
        request._audit_start_time = time.time()
        return None

    def process_response(self, request, response):
        """レスポンス処理完了時"""
        # 除外パスのチェック
        if self._should_exclude(request):
            return response

        # 監査ログの作成
        try:
            self._create_audit_log(request, response)
        except Exception as e:
            # ログ作成エラーは無視（サービスに影響を与えない）
            print(f"Error creating audit log: {e}")

        return response

    def _should_exclude(self, request):
        """ログ対象外かどうかを判定"""
        # メソッドチェック
        if request.method in self.EXCLUDED_METHODS:
            return True

        # パスチェック
        path = request.path
        for excluded_path in self.EXCLUDED_PATHS:
            if path.startswith(excluded_path):
                return True

        return False

    def _create_audit_log(self, request, response):
        """監査ログを作成"""
        # レスポンス時間を計算
        response_time = 0
        if hasattr(request, '_audit_start_time'):
            response_time = int((time.time() - request._audit_start_time) * 1000)

        # アクションタイプを決定
        action_type = self._determine_action_type(request)

        # リソース情報を抽出
        resource_type, resource_id = self._extract_resource_info(request)

        # ユーザー情報
        user = request.user if request.user.is_authenticated else None
        user_email = user.email if user else ''
        user_role = getattr(user, 'role', '') if user else ''

        # リクエストパラメータを取得
        request_params = self._get_request_params(request)

        # 説明文を生成
        description = self._generate_description(request, action_type, resource_type)

        # 重要度を決定
        severity = self._determine_severity(request, response)

        # 不審なアクティビティをチェック
        is_suspicious = self._check_suspicious_activity(request, response)

        # 監査ログを保存
        AuditLog.objects.create(
            user=user,
            user_email=user_email,
            user_role=user_role,
            action_type=action_type,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            request_method=request.method,
            request_path=request.path[:500],
            request_params=request_params,
            status_code=response.status_code,
            response_time_ms=response_time,
            severity=severity,
            is_suspicious=is_suspicious,
            is_success=200 <= response.status_code < 400,
            error_message=self._get_error_message(response),
        )

    def _determine_action_type(self, request):
        """HTTPメソッドからアクションタイプを決定"""
        method = request.method
        path = request.path

        if 'login' in path.lower():
            return 'login'
        elif 'logout' in path.lower():
            return 'logout'
        elif 'export' in path.lower():
            return 'export'
        elif 'download' in path.lower():
            return 'download'

        mapping = {
            'GET': 'read',
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete',
        }
        return mapping.get(method, 'read')

    def _extract_resource_info(self, request):
        """URLパスからリソース情報を抽出"""
        path = request.path
        parts = [p for p in path.split('/') if p]

        if len(parts) == 0:
            return 'root', ''

        # API エンドポイントの場合
        if parts[0] == 'api':
            if len(parts) > 1:
                resource_type = parts[1]
                resource_id = parts[2] if len(parts) > 2 and parts[2].isdigit() else ''
                return resource_type, resource_id

        return parts[0], ''

    def _get_request_params(self, request):
        """リクエストパラメータを取得（機密情報を除く）"""
        params = {}

        # GETパラメータ
        if request.GET:
            params['query_params'] = dict(request.GET)

        # POSTデータ（JSONまたはフォームデータ）
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                if request.content_type == 'application/json':
                    body = json.loads(request.body.decode('utf-8'))
                    # パスワードなどの機密情報を除外
                    params['body'] = self._sanitize_sensitive_data(body)
                elif request.POST:
                    params['body'] = self._sanitize_sensitive_data(dict(request.POST))
            except:
                pass

        return params

    def _sanitize_sensitive_data(self, data):
        """機密データをサニタイズ"""
        sensitive_fields = ['password', 'token', 'secret', 'api_key', 'credit_card']

        if isinstance(data, dict):
            sanitized = {}
            for key, value in data.items():
                if any(field in key.lower() for field in sensitive_fields):
                    sanitized[key] = '***REDACTED***'
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_sensitive_data(value)
                elif isinstance(value, list):
                    sanitized[key] = [self._sanitize_sensitive_data(item) if isinstance(item, dict) else item for item in value]
                else:
                    sanitized[key] = value
            return sanitized

        return data

    def _generate_description(self, request, action_type, resource_type):
        """アクションの説明を生成"""
        user = request.user if request.user.is_authenticated else None
        user_str = user.email if user else 'Anonymous'

        action_map = {
            'create': '作成',
            'read': '閲覧',
            'update': '更新',
            'delete': '削除',
            'login': 'ログイン',
            'logout': 'ログアウト',
            'export': 'エクスポート',
            'download': 'ダウンロード',
        }

        action_jp = action_map.get(action_type, action_type)
        return f"{user_str} が {resource_type} を{action_jp}しました"

    def _determine_severity(self, request, response):
        """重要度を決定"""
        # エラーレスポンス
        if response.status_code >= 500:
            return 'critical'
        elif response.status_code >= 400:
            return 'medium'

        # 機密操作
        if request.method in ['DELETE', 'POST'] and 'admin' in request.path:
            return 'high'

        # データエクスポート
        if 'export' in request.path.lower() or 'download' in request.path.lower():
            return 'high'

        return 'low'

    def _check_suspicious_activity(self, request, response):
        """不審なアクティビティをチェック"""
        # 多数の失敗したログイン試行
        if 'login' in request.path.lower() and response.status_code >= 400:
            return True

        # 権限エラー
        if response.status_code in [401, 403]:
            return True

        return False

    def _get_client_ip(self, request):
        """クライアントのIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _get_error_message(self, response):
        """エラーメッセージを取得"""
        if response.status_code >= 400:
            try:
                if hasattr(response, 'data'):
                    return str(response.data)[:500]
                elif hasattr(response, 'content'):
                    content = response.content.decode('utf-8')
                    return content[:500]
            except:
                pass
        return ''


class DataAccessMiddleware(MiddlewareMixin):
    """
    個人情報アクセスログミドルウェア
    個人情報へのアクセスを記録します。
    """

    # 個人情報を含むエンドポイント
    SENSITIVE_ENDPOINTS = [
        '/api/candidates/',
        '/api/applications/',
        '/api/interviews/',
    ]

    def process_response(self, request, response):
        """レスポンス処理完了時"""
        # 認証済みユーザーのみ
        if not request.user.is_authenticated:
            return response

        # 個人情報エンドポイントのチェック
        if not self._is_sensitive_endpoint(request.path):
            return response

        # GETリクエスト（閲覧）のみログ
        if request.method != 'GET':
            return response

        # 成功レスポンスのみ
        if response.status_code != 200:
            return response

        try:
            self._create_data_access_log(request)
        except Exception as e:
            print(f"Error creating data access log: {e}")

        return response

    def _is_sensitive_endpoint(self, path):
        """個人情報エンドポイントかどうか"""
        return any(path.startswith(endpoint) for endpoint in self.SENSITIVE_ENDPOINTS)

    def _create_data_access_log(self, request):
        """データアクセスログを作成"""
        # アクセスタイプを決定
        access_type = 'view'
        if 'export' in request.path.lower():
            access_type = 'export'
        elif 'download' in request.path.lower():
            access_type = 'download'

        # ログを保存
        DataAccessLog.objects.create(
            user=request.user,
            target_user=None,  # 実際のアプリケーションでは対象ユーザーを特定
            access_type=access_type,
            accessed_fields=[],  # 実際のアプリケーションではアクセスしたフィールドを記録
            purpose='API access',
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            is_authorized=True,
            is_gdpr_compliant=True,
        )

    def _get_client_ip(self, request):
        """クライアントのIPアドレスを取得"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
