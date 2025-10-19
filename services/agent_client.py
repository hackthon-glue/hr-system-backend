"""
AWS Bedrock AgentCore クライアント
agentcore CLIを使用してAgentCoreと通信
"""
import json
import logging
import subprocess
import os
from typing import Dict, Any, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)


class AgentCoreClient:
    """AWS Bedrock AgentCore クライアント"""

    def __init__(self):
        """クライアントを初期化"""
        self.region = settings.AWS_REGION
        self.agent_id = settings.AWS_BEDROCK_AGENT_ID
        self.aws_profile = getattr(settings, 'AWS_PROFILE', 'w')

        # agentcore CLIのパスを設定
        self.agentcore_path = self._find_agentcore_cli()

        logger.info(f"AgentCore client initialized")
        logger.info(f"AWS Profile: {self.aws_profile}")
        logger.info(f"Region: {self.region}")
        logger.info(f"Agent ID: {self.agent_id}")
        logger.info(f"AgentCore CLI path: {self.agentcore_path}")

    def _find_agentcore_cli(self) -> str:
        """agentcore CLIのパスを検索"""
        # agents/.venv内のagentcoreを優先
        agents_venv_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'agents',
            '.venv',
            'bin',
            'agentcore'
        )

        if os.path.exists(agents_venv_path):
            return agents_venv_path

        # システムのagentcoreを使用
        return 'agentcore'

    def is_available(self) -> bool:
        """AgentCoreが利用可能かチェック"""
        # AWS_BEDROCK_AGENT_IDが設定されていれば利用可能
        # App Runnerの場合、IAMロールで認証するためAWS_PROFILEは不要
        has_agent_id = bool(self.agent_id)

        return has_agent_id

    def invoke_agent(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        qualifier: str = "DEFAULT",
        enable_trace: bool = False
    ) -> Dict[str, Any]:
        """
        AgentCoreランタイムを呼び出し

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
            logger.warning("AgentCore is not available, returning mock response")
            return self._mock_response(prompt)

        try:
            # セッションIDが指定されていない場合は生成
            if not session_id:
                import uuid
                session_id = str(uuid.uuid4())

            # agentcore invokeコマンドを実行
            payload = {"prompt": prompt}
            payload_json = json.dumps(payload)

            # 環境変数の設定
            env = os.environ.copy()
            # AWS_PROFILEが設定されている場合のみ追加（App RunnerではIAMロールを使用）
            if self.aws_profile:
                env['AWS_PROFILE'] = self.aws_profile

            # agentcoreディレクトリに移動して実行
            agents_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                'agents'
            )

            logger.info(f"Invoking AgentCore with prompt: {prompt[:100]}...")
            logger.info(f"Using agents directory: {agents_dir}")
            logger.info(f"Payload: {payload_json}")

            # agentcore invokeを実行
            result = subprocess.run(
                [self.agentcore_path, 'invoke', payload_json],
                cwd=agents_dir,
                env=env,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode != 0:
                logger.error(f"AgentCore invoke failed with return code: {result.returncode}")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error(f"STDERR: {result.stderr}")
                raise Exception(f"AgentCore invocation failed: {result.stderr}")

            # 出力をパース
            output = result.stdout.strip()
            logger.info(f"AgentCore raw output (first 500 chars): {output[:500]}")

            # "Response:" 以降のJSONを抽出
            json_str = output
            if 'Response:' in output:
                # "Response:" 以降の部分を取得
                json_str = output.split('Response:', 1)[1].strip()
                # 改行を削除してJSON文字列を一行にする
                # (agentcore invokeの出力はプリティプリントされている可能性がある)
                json_str = ' '.join(json_str.split())
                logger.info(f"Extracted JSON (first 500 chars): {json_str[:500]}")

            # JSONとしてパース
            try:
                # まず外側のJSONをパース
                response_data = json.loads(json_str)
                result_str = response_data.get('result', json_str)

                logger.info(f"Parsed outer JSON, result type: {type(result_str)}")
                logger.info(f"Result str (first 200 chars): {repr(result_str[:200]) if isinstance(result_str, str) else str(result_str)[:200]}")

                # resultの値がJSON文字列の場合、さらにパース
                try:
                    if isinstance(result_str, str):
                        # 内側のJSON文字列をパース
                        completion_obj = json.loads(result_str)
                        # パースに成功した場合、JSON文字列として返す（hr_agent_servicesで再度パースするため）
                        completion_text = json.dumps(completion_obj, ensure_ascii=False)
                        logger.info(f"Successfully parsed inner JSON")
                    else:
                        completion_text = json.dumps(result_str, ensure_ascii=False)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse inner JSON: {e}")
                    logger.warning(f"Inner JSON string repr: {repr(result_str[:200]) if isinstance(result_str, str) else str(result_str)[:200]}")
                    # パースできない場合はそのまま使用
                    completion_text = result_str

            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                logger.error(f"Failed to parse: {json_str[:500]}")
                logger.error(f"JSON str repr: {repr(json_str[:200])}")
                # JSONでない場合はそのまま使用
                completion_text = json_str

            logger.info(f"AgentCore invocation successful")
            logger.info(f"Completion length: {len(completion_text)}")

            return {
                'completion': completion_text,
                'raw_result': {'text': completion_text},
                'session_id': session_id,
                'content_type': 'application/json'
            }

        except subprocess.TimeoutExpired:
            logger.error("AgentCore invocation timed out")
            raise Exception("AgentCore invocation timed out after 120 seconds")

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
