"""
AWS Bedrock AgentCore クライアント
agentcore CLI を使用してBedrock AgentCoreと通信
"""
import json
import logging
import subprocess
import uuid
import shutil
import os
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

        # Agent name (for agentcore CLI --agent parameter)
        self.agent_name = "HrAgent"

        if self.agentcore_path:
            logger.info(f"AgentCore CLI found at: {self.agentcore_path}")
            logger.info(f"Region: {self.region}")
            logger.info(f"Runtime ID: {self.runtime_id}")
            logger.info(f"Agent Name: {self.agent_name}")
        else:
            logger.warning("AgentCore CLI not found in PATH")

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
                session_id = f"{session_id}-{uuid.uuid4().hex}"[:50]

            logger.info(f"Invoking AgentCore CLI with prompt: {prompt[:100]}...")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Agent Name: {self.agent_name}")

            # Payloadを構築
            payload = {
                "prompt": prompt
            }
            payload_json = json.dumps(payload)

            # 環境変数を設定
            env = os.environ.copy()
            env['AWS_REGION'] = self.region

            # AWS_PROFILE が設定されている場合は使用（ローカル開発用）
            if 'AWS_PROFILE' in os.environ:
                env['AWS_PROFILE'] = os.environ['AWS_PROFILE']
                logger.info(f"Using AWS_PROFILE: {os.environ['AWS_PROFILE']}")
            else:
                logger.info(f"Using Instance Role credentials")

            # agentcore invoke コマンドを実行
            cmd = [
                self.agentcore_path,
                'invoke',
                payload_json,
                '--agent', self.agent_name,
                '--session-id', session_id
            ]

            logger.debug(f"Executing command: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
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

            # 変数を初期化
            response_data = {}
            completion_text = ""

            # JSON レスポンスを抽出
            # AgentCore CLIはボックス出力 + "Response:\n" + JSON を返す
            if "Response:" in output:
                # "Response:" の後のJSON部分のみを抽出
                response_marker_idx = output.rfind("Response:")  # 最後のResponse:を探す
                json_str = output[response_marker_idx + len("Response:"):].strip()
                logger.debug(f"Extracted JSON after 'Response:' (first 200 chars): {json_str[:200]}")

                try:
                    # AgentCoreは {"result": "actual response text"} の形式で返す
                    # ただし、resultの値は文字列として返され、その中に実際の改行が含まれている可能性がある
                    # そのため、strict=Falseを使用して柔軟にパースする
                    response_data = json.loads(json_str, strict=False)
                    logger.debug(f"Successfully parsed JSON from Response marker")

                    # response_dataが {"result": "..."} 形式の場合、resultの値を取得
                    if 'result' in response_data and isinstance(response_data['result'], str):
                        # resultフィールドの値を取得（これが実際のAgent応答）
                        completion_text = response_data['result']
                        logger.debug(f"Extracted completion from 'result' field, length: {len(completion_text)}")
                    else:
                        # それ以外の場合、response_data全体をJSON文字列として返す
                        completion_text = json.dumps(response_data, ensure_ascii=False)
                        logger.debug(f"Using entire response_data as completion")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON after 'Response:' marker: {e}")
                    logger.error(f"Problematic JSON string (first 300 chars): {json_str[:300]}")

                    # JSON parse失敗：json_strをそのまま返す（これ自体がJSONかもしれない）
                    completion_text = json_str
                    response_data = {"raw_response": json_str}
            else:
                # "Response:"がない場合は、全体をそのまま使用
                logger.warning("No 'Response:' marker found in AgentCore output")
                completion_text = output

            logger.info(f"AgentCore invocation successful")
            logger.info(f"Completion length: {len(completion_text)}")
            logger.info(f"Completion preview: {completion_text[:200] if completion_text else 'EMPTY'}")

            # 空のレスポンスチェック
            if not completion_text or not completion_text.strip():
                logger.error("AgentCore returned empty completion text")
                logger.error(f"Raw output was: {output[:500]}")

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
        # 面接質問生成の場合は適切なJSON形式を返す
        if "Generate" in prompt and "interview questions" in prompt:
            mock_questions = {
                "questions": [
                    {
                        "id": 1,
                        "question_text": "Tell me about your previous work experience and key achievements.",
                        "question_type": "general",
                        "difficulty": "medium",
                        "order": 1,
                        "expected_answer": "Specific examples of work experience with quantifiable results",
                        "evaluation_criteria": "Specificity, clarity, and relevance to the position"
                    },
                    {
                        "id": 2,
                        "question_text": "What technical skills do you possess that are relevant to this role?",
                        "question_type": "technical",
                        "difficulty": "medium",
                        "order": 2,
                        "expected_answer": "Concrete technical skills with experience level",
                        "evaluation_criteria": "Depth of knowledge and practical application"
                    },
                    {
                        "id": 3,
                        "question_text": "Describe a challenging situation you faced at work and how you resolved it.",
                        "question_type": "behavioral",
                        "difficulty": "medium",
                        "order": 3,
                        "expected_answer": "STAR method (Situation, Task, Action, Result)",
                        "evaluation_criteria": "Problem-solving ability and leadership skills"
                    },
                    {
                        "id": 4,
                        "question_text": "Why are you interested in this position and our company?",
                        "question_type": "general",
                        "difficulty": "easy",
                        "order": 4,
                        "expected_answer": "Understanding of company and motivation for application",
                        "evaluation_criteria": "Research effort and genuine interest"
                    },
                    {
                        "id": 5,
                        "question_text": "What are your career goals for the next 3-5 years?",
                        "question_type": "general",
                        "difficulty": "easy",
                        "order": 5,
                        "expected_answer": "Clear career vision aligned with the role",
                        "evaluation_criteria": "Alignment with company direction and growth potential"
                    }
                ]
            }
            completion_text = json.dumps(mock_questions, ensure_ascii=False)
        # 面接評価の場合
        elif "evaluate" in prompt.lower() and "interview" in prompt.lower():
            mock_evaluation = {
                "evaluation_report": {
                    "overall_score": 7,
                    "strengths": [
                        "Clear communication skills",
                        "Relevant technical background",
                        "Good problem-solving approach"
                    ],
                    "areas_for_improvement": [
                        "Could provide more specific examples",
                        "Needs more depth in advanced topics"
                    ],
                    "recommendation": "合格",
                    "comment": "[MOCK RESPONSE] The candidate demonstrated solid technical knowledge and communication skills. Their answers were clear and relevant to the position. With more experience in complex projects, they have strong potential for growth in this role."
                }
            }
            completion_text = json.dumps(mock_evaluation, ensure_ascii=False)
        # 求人マッチングの場合
        elif "match" in prompt.lower() and "job" in prompt.lower():
            mock_matching = {
                "recommended_jobs": [
                    {
                        "job_id": 1,
                        "job_title": "Backend Engineer",
                        "skill_match": 85,
                        "experience_match": 80,
                        "salary_match": 90,
                        "overall_match": 85,
                        "match_reason": "[MOCK] Strong technical background in Python and Django",
                        "concerns": "May need additional cloud experience"
                    }
                ],
                "summary": "[MOCK] 1 highly matched position found"
            }
            completion_text = json.dumps(mock_matching, ensure_ascii=False)
        else:
            # 一般的なモックレスポンス
            completion_text = f"[MOCK] This is a mock response for development. AgentCore CLI is not available. Prompt preview: {prompt[:100]}..."

        return {
            'completion': completion_text,
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