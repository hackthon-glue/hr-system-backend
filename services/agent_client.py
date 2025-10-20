"""
AWS Bedrock Agent Runtime クライアント
boto3を使用してBedrock Agent Runtimeと直接通信
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AgentCoreClient:
    """AWS Bedrock Agent Runtime クライアント"""

    def __init__(self):
        """クライアントを初期化"""
        self.region = settings.AWS_REGION
        self.agent_id = settings.AWS_BEDROCK_AGENT_ID

        # boto3クライアントを初期化
        try:
            import boto3
            self.client = boto3.client(
                'bedrock-agent-runtime',
                region_name=self.region
            )
            logger.info(f"Bedrock Agent Runtime client initialized")
            logger.info(f"Region: {self.region}")
            logger.info(f"Agent ID: {self.agent_id}")
        except Exception as e:
            logger.error(f"Failed to initialize boto3 client: {e}", exc_info=True)
            self.client = None

    def is_available(self) -> bool:
        """Bedrock Agentが利用可能かチェック"""
        has_client = self.client is not None
        has_agent_id = bool(self.agent_id)

        is_avail = has_client and has_agent_id
        if not is_avail:
            logger.warning(f"Bedrock Agent not available: client={has_client}, agent_id={has_agent_id}")

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
        Bedrock Agent Runtimeを呼び出し

        Args:
            prompt: 入力プロンプト
            session_id: セッションID（会話の継続に使用）
            user_id: ユーザーID
            qualifier: エンドポイント識別子（デフォルト: DEFAULT）
            enable_trace: トレースを有効化

        Returns:
            エージェントからのレスポンス
        """
        if not self.is_available():
            logger.warning("Bedrock Agent is not available, returning mock response")
            return self._mock_response(prompt)

        try:
            # セッションIDが指定されていない場合は生成
            if not session_id:
                session_id = str(uuid.uuid4())

            logger.info(f"Invoking Bedrock Agent with prompt: {prompt[:100]}...")
            logger.info(f"Session ID: {session_id}")

            # Bedrock Agent Runtimeを呼び出し
            response = self.client.invoke_agent(
                agentId=self.agent_id,
                agentAliasId='TSTALIASID',  # Test alias
                sessionId=session_id,
                inputText=prompt,
                enableTrace=enable_trace
            )

            # ストリーミングレスポンスを処理
            completion_text = ""
            event_stream = response.get('completion', [])

            for event in event_stream:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        text = chunk['bytes'].decode('utf-8')
                        completion_text += text
                        logger.debug(f"Received chunk: {text[:100]}")

            logger.info(f"Bedrock Agent invocation successful")
            logger.info(f"Completion length: {len(completion_text)}")

            return {
                'completion': completion_text,
                'raw_result': {'text': completion_text},
                'session_id': session_id,
                'content_type': 'text/plain'
            }

        except Exception as e:
            logger.error(f"Unexpected error invoking agent: {e}", exc_info=True)
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
