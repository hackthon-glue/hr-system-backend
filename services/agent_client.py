"""
AWS Bedrock AgentCore クライアント
boto3を使用してBedrock AgentCoreと直接通信
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AgentCoreClient:
    """AWS Bedrock AgentCore クライアント"""

    def __init__(self):
        """クライアントを初期化"""
        self.region = settings.AWS_REGION
        self.runtime_id = settings.AWS_BEDROCK_AGENT_ID  # Runtime ID (e.g., HrAgent-uVxcle2LzN)
        self.account_id = "553113730995"  # AWS Account ID

        # Agent Runtime ARNを構築
        self.agent_runtime_arn = f"arn:aws:bedrock-agentcore:{self.region}:{self.account_id}:runtime/{self.runtime_id}"

        # boto3クライアントを初期化
        try:
            import boto3
            self.client = boto3.client(
                'bedrock-agentcore',
                region_name=self.region
            )
            logger.info(f"Bedrock AgentCore client initialized")
            logger.info(f"Region: {self.region}")
            logger.info(f"Runtime ID: {self.runtime_id}")
            logger.info(f"Agent Runtime ARN: {self.agent_runtime_arn}")
        except Exception as e:
            logger.error(f"Failed to initialize boto3 client: {e}", exc_info=True)
            self.client = None

    def is_available(self) -> bool:
        """Bedrock AgentCoreが利用可能かチェック"""
        has_client = self.client is not None
        has_runtime_id = bool(self.runtime_id)

        is_avail = has_client and has_runtime_id
        if not is_avail:
            logger.warning(f"Bedrock AgentCore not available: client={has_client}, runtime_id={has_runtime_id}")

        return is_avail

    def invoke_agent(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        qualifier: str = "DEFAULT",
        enable_trace: bool = False
    ) -> Dict[str, Any]:
        """
        Bedrock AgentCoreを呼び出し

        Args:
            prompt: 入力プロンプト
            session_id: セッションID（会話の継続に使用、33文字以上必要）
            user_id: ユーザーID
            qualifier: エンドポイント識別子（デフォルト: DEFAULT）
            enable_trace: トレースを有効化

        Returns:
            エージェントからのレスポンス
        """
        if not self.is_available():
            logger.error("Bedrock AgentCore is not available")
            raise Exception("Bedrock AgentCore is not configured properly")

        try:
            # セッションIDが指定されていない場合は生成（33文字以上）
            if not session_id:
                session_id = f"{user_id or 'user'}-{uuid.uuid4().hex}"

            # セッションIDが33文字未満の場合は調整
            if len(session_id) < 33:
                session_id = f"{session_id}-{uuid.uuid4().hex}"[:50]

            logger.info(f"Invoking Bedrock AgentCore with prompt: {prompt[:100]}...")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Agent Runtime ARN: {self.agent_runtime_arn}")

            # Payloadを構築
            payload = json.dumps({
                "input": {"prompt": prompt}
            })

            # Bedrock AgentCoreを呼び出し
            response = self.client.invoke_agent_runtime(
                agentRuntimeArn=self.agent_runtime_arn,
                runtimeSessionId=session_id,
                payload=payload,
                qualifier=qualifier
            )

            # レスポンスボディを読み取り
            response_body = response['response'].read()
            response_data = json.loads(response_body)

            # Completionテキストを抽出
            completion_text = response_data.get('output', {}).get('text', '') if isinstance(response_data.get('output'), dict) else str(response_data.get('output', ''))

            # 空の場合は別のフィールドを試す
            if not completion_text:
                completion_text = response_data.get('result', '') or str(response_data)

            logger.info(f"Bedrock AgentCore invocation successful")
            logger.info(f"Completion length: {len(completion_text)}")

            return {
                'completion': completion_text,
                'raw_result': response_data,
                'session_id': session_id,
                'content_type': 'application/json'
            }

        except Exception as e:
            logger.error(f"Unexpected error invoking AgentCore: {e}", exc_info=True)
            raise

    def invoke_with_retry(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        リトライ機能付きでエージェントを呼び出し

        Args:
            prompt: 入力プロンプト
            session_id: セッションID
            user_id: ユーザーID
            max_retries: 最大リトライ回数
            **kwargs: その他のパラメータ

        Returns:
            エージェントからのレスポンス
        """
        last_exception = None

        for attempt in range(max_retries):
            try:
                return self.invoke_agent(
                    prompt=prompt,
                    session_id=session_id,
                    user_id=user_id,
                    **kwargs
                )
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")

                if attempt < max_retries - 1:
                    # 指数バックオフ
                    import time
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)

        # すべてのリトライが失敗
        logger.error(f"All {max_retries} attempts failed")
        raise last_exception

    def _mock_response(self, prompt: str) -> Dict[str, Any]:
        """
        モックレスポンスを返す（開発用）

        Args:
            prompt: 入力プロンプト

        Returns:
            モックレスポンス
        """
        return {
            'completion': f"[MOCK] Processed: {prompt}",
            'raw_result': {},
            'session_id': 'mock-session',
            'content_type': 'application/json',
            'is_mock': True
        }


class AgentSession:
    """エージェントセッション管理"""

    def __init__(self, user_id: str, agent_type: str):
        """
        セッションを初期化

        Args:
            user_id: ユーザーID
            agent_type: エージェントタイプ
        """
        import uuid
        self.user_id = user_id
        self.agent_type = agent_type
        # AgentCore requires session ID with min length 33
        self.session_id = f"{user_id}-{agent_type}-{uuid.uuid4().hex}"
        self.history: List[Dict[str, Any]] = []

    def add_interaction(self, user_input: str, agent_response: str):
        """
        インタラクションを履歴に追加

        Args:
            user_input: ユーザー入力
            agent_response: エージェントレスポンス
        """
        self.history.append({
            'user_input': user_input,
            'agent_response': agent_response,
            'timestamp': self._get_timestamp()
        })

    def get_context(self) -> Dict[str, Any]:
        """
        セッションコンテキストを取得

        Returns:
            セッションコンテキスト
        """
        return {
            'user_id': self.user_id,
            'agent_type': self.agent_type,
            'session_id': self.session_id,
            'history_count': len(self.history),
            'recent_interactions': self.history[-5:]  # 直近5件
        }

    @staticmethod
    def _get_timestamp() -> str:
        """現在のタイムスタンプを取得"""
        from datetime import datetime
        return datetime.now().isoformat()


# グローバルクライアントインスタンス
_agent_client: Optional[AgentCoreClient] = None


def get_agent_client() -> AgentCoreClient:
    """
    AgentCoreクライアントのシングルトンインスタンスを取得

    Returns:
        AgentCoreClient インスタンス
    """
    global _agent_client
    if _agent_client is None:
        _agent_client = AgentCoreClient()
    return _agent_client
