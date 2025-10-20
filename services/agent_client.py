"""
AWS Bedrock AgentCore クライアント
agentcore CLI を使用してBedrock AgentCoreと通信
"""
import json
import logging
import subprocess
import uuid
import shutil
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AgentCoreClient:
    """AWS Bedrock AgentCore クライアント"""

    def __init__(self):
        """クライアントを初期化"""
        self.region = settings.AWS_REGION
        self.runtime_id = settings.AWS_BEDROCK_AGENT_ID  # Runtime ID (e.g., HrAgent-uVxcle2LzN)

        # agentcore CLI のパスを取得
        self.agentcore_path = shutil.which('agentcore')

        if self.agentcore_path:
            logger.info(f"AgentCore CLI found at: {self.agentcore_path}")
            logger.info(f"Region: {self.region}")
            logger.info(f"Runtime ID: {self.runtime_id}")
        else:
            logger.error("AgentCore CLI not found in PATH")

    def is_available(self) -> bool:
        """Bedrock AgentCoreが利用可能かチェック"""
        has_cli = self.agentcore_path is not None
        has_runtime_id = bool(self.runtime_id)

        is_avail = has_cli and has_runtime_id
        if not is_avail:
            logger.warning(f"Bedrock AgentCore not available: cli={has_cli}, runtime_id={has_runtime_id}")

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
            logger.warning("AgentCore CLI is not available, returning mock response")
            return self._mock_response(prompt)

        try:
            # セッションIDが指定されていない場合は生成（33文字以上）
            if not session_id:
                session_id = f"{user_id or 'user'}-{uuid.uuid4().hex}"

            # セッションIDが33文字未満の場合は調整
            if len(session_id) < 33:
                session_id = f"{session_id}-{uuid.uuid4().hex}"[:33]

            logger.info(f"Invoking AgentCore CLI with prompt: {prompt[:100]}...")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Runtime ID: {self.runtime_id}")

            # Payloadを構築
            payload = {
                "prompt": prompt,
                "sessionId": session_id
            }
            payload_json = json.dumps(payload)

            # agentcore invoke コマンドを実行
            # AWS_REGION を環境変数として渡す
            import os
            env = os.environ.copy()
            env['AWS_REGION'] = self.region

            result = subprocess.run(
                [self.agentcore_path, 'invoke', payload_json],
                capture_output=True,
                text=True,
                timeout=120,
                env=env
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"AgentCore CLI failed: {error_msg}")
                raise Exception(f"AgentCore CLI error: {error_msg}")

            # 出力をパース
            output = result.stdout.strip()
            logger.debug(f"AgentCore CLI output: {output[:500]}")

            # JSON レスポンスを抽出
            try:
                # "Response:" の後のJSON部分を抽出
                if "Response:" in output:
                    json_start = output.index("Response:") + len("Response:")
                    json_str = output[json_start:].strip()
                    response_data = json.loads(json_str)
                else:
                    # 全体をJSONとしてパース
                    response_data = json.loads(output)
            except json.JSONDecodeError:
                # JSONパースに失敗した場合は、出力全体をテキストとして扱う
                logger.warning(f"Failed to parse JSON, using raw output")
                response_data = {"result": output}

            # Completionテキストを抽出
            completion_text = response_data.get('result', '') or response_data.get('output', {}).get('text', '') or str(response_data)

            logger.info(f"AgentCore invocation successful")
            logger.info(f"Completion length: {len(completion_text)}")

            return {
                'completion': completion_text,
                'raw_result': response_data,
                'session_id': session_id,
                'content_type': 'text/plain'
            }

        except subprocess.TimeoutExpired:
            logger.error(f"AgentCore CLI timeout after 120 seconds")
            raise Exception("AgentCore CLI timeout")
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
