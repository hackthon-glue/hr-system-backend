"""
HR エージェントサービス層
各種HR関連タスクをAgentCoreに依頼
"""
import json
import logging
from typing import Dict, Any, List, Optional
from .agent_client import get_agent_client, AgentSession

logger = logging.getLogger(__name__)


class BaseAgentService:
    """エージェントサービス基底クラス"""

    def __init__(self, agent_type: str):
        """
        サービスを初期化

        Args:
            agent_type: エージェントタイプ
        """
        self.agent_type = agent_type
        self.client = get_agent_client()

    def invoke(
        self,
        user_id: str,
        prompt: str,
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        エージェントを呼び出し

        Args:
            user_id: ユーザーID
            prompt: プロンプト
            session_id: セッションID（省略時は自動生成）
            context: 追加コンテキスト

        Returns:
            エージェントのレスポンス
        """
        if not session_id:
            session = AgentSession(user_id, self.agent_type)
            session_id = session.session_id

        # コンテキストがあれば、プロンプトに追加
        full_prompt = self._build_prompt(prompt, context)

        try:
            response = self.client.invoke_with_retry(
                prompt=full_prompt,
                session_id=session_id,
                user_id=user_id
            )

            return {
                'success': True,
                'response': response.get('completion', ''),
                'session_id': session_id,
                'agent_type': self.agent_type,
                'is_mock': response.get('is_mock', False)
            }

        except Exception as e:
            logger.error(f"Error invoking {self.agent_type} agent: {e}")
            return {
                'success': False,
                'error': str(e),
                'session_id': session_id,
                'agent_type': self.agent_type
            }

    def _build_prompt(self, prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        プロンプトを構築

        Args:
            prompt: 基本プロンプト
            context: 追加コンテキスト

        Returns:
            完成したプロンプト
        """
        if not context:
            return prompt

        import json
        context_str = json.dumps(context, ensure_ascii=False, indent=2)
        return f"{prompt}\n\n[Context Information]\n{context_str}"


class ConciergeService(BaseAgentService):
    """候補者コンシェルジュサービス"""

    def __init__(self):
        super().__init__("concierge")

    def assist_candidate(
        self,
        user_id: str,
        query: str,
        candidate_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        候補者をアシスト

        Args:
            user_id: ユーザーID
            query: 問い合わせ内容
            candidate_info: 候補者情報

        Returns:
            アシスタントのレスポンス
        """
        prompt = f"""
This is an inquiry from a candidate. Please provide kind and specific advice.

[Inquiry]
{query}
"""
        return self.invoke(user_id, prompt, context=candidate_info)

    def career_advice(
        self,
        user_id: str,
        question: str,
        career_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        キャリアアドバイスを提供

        Args:
            user_id: ユーザーID
            question: キャリアに関する質問
            career_history: 職歴情報

        Returns:
            キャリアアドバイス
        """
        prompt = f"""
This is a career consultation from a candidate.

[Question]
{question}

Please provide kind and practical advice.
"""
        context = {'career_history': career_history} if career_history else None
        return self.invoke(user_id, prompt, context=context)


class SkillParserService(BaseAgentService):
    """スキル解析サービス"""

    def __init__(self):
        super().__init__("skill_parser")

    def parse_resume(
        self,
        user_id: str,
        resume_text: str
    ) -> Dict[str, Any]:
        """
        履歴書からスキルを抽出

        Args:
            user_id: ユーザーID
            resume_text: 履歴書テキスト

        Returns:
            抽出されたスキル情報
        """
        prompt = f"""
以下の履歴書からスキルと経験を抽出してください。

【履歴書】
{resume_text}

以下の形式で抽出してください：
1. **技術スキル**（プログラミング言語、フレームワーク、データベース、クラウドなど）
2. **ソフトスキル**（コミュニケーション、リーダーシップなど）
3. **経験レベル**（各スキルの熟練度と使用年数）
4. **資格・認定**

JSON形式でも出力してください。
"""
        return self.invoke(user_id, prompt)

    def parse_github_profile(
        self,
        user_id: str,
        github_url: str
    ) -> Dict[str, Any]:
        """
        GitHubプロフィールからスキルを抽出

        Args:
            user_id: ユーザーID
            github_url: GitHub URL

        Returns:
            抽出されたスキル情報
        """
        prompt = f"""
GitHubプロフィール（{github_url}）から技術スキルを分析してください。

以下を抽出：
1. 使用言語とその比率
2. 主要なプロジェクト
3. コントリビューション傾向
4. 技術スタック

注: 実際のGitHub APIアクセスが必要な場合は適切なツールを使用してください。
"""
        return self.invoke(user_id, prompt)


class JobMatcherService(BaseAgentService):
    """求人マッチングサービス"""

    def __init__(self):
        super().__init__("job_matcher")

    def match_candidate_to_jobs(
        self,
        user_id: str,
        candidate_profile: Dict[str, Any],
        available_jobs: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        候補者と求人をマッチング

        Args:
            user_id: ユーザーID
            candidate_profile: 候補者プロフィール
            available_jobs: 求人リスト

        Returns:
            マッチング結果
        """
        prompt = f"""
あなたは優秀な人材マッチングAIです。候補者のプロフィールと求人リストを分析して、最適な求人をマッチングしてください。

【分析タスク】
候補者の経験・スキルと各求人を照らし合わせて、以下の観点で評価してください：
1. スキルマッチ度（0-100%）
2. 経験年数の適合度（0-100%）
3. 給与条件の適合度（0-100%）
4. 総合マッチ度（0-100%）
5. マッチング理由（簡潔に）
6. 懸念事項があれば記載

【重要】必ず以下のJSON形式で応答してください（他の文章は不要）：

{{
  "recommended_jobs": [
    {{
      "job_id": "数値のID（例: 1, 2, 3など。job_codeではなく、idフィールドの値を使用）",
      "job_title": "求人タイトル",
      "skill_match": 85,
      "experience_match": 90,
      "salary_match": 80,
      "overall_match": 85,
      "match_reason": "Pythonとデータ分析の経験が豊富",
      "concerns": "リモートワークの希望と異なる"
    }}
  ],
  "summary": "○件の高マッチ度求人が見つかりました"
}}

注意: job_idは必ず数値のid（例: 1, 2, 3）を使用してください。job_code（例: JOB-2025-001）は使用しないでください。

JSON形式のみで応答してください。
"""
        context = {
            'candidate': candidate_profile,
            'jobs': available_jobs
        }

        # エージェントを呼び出し
        result = self.invoke(user_id, prompt, context=context)

        # レスポンスが成功した場合、JSON文字列をパースして構造化データとして返す
        if result.get('success'):
            # 'response' は BaseAgentService.invoke() が返すキー
            # 実際の completion テキストを取得
            response_text = result.get('response', '')

            try:
                # JSON文字列をパース
                logger.info(f"Parsing response_text type: {type(response_text)}")
                logger.info(f"Response text sample: {response_text[:200]}")

                parsed_data = json.loads(response_text)
                logger.info(f"First parse result type: {type(parsed_data)}")

                # AgentCore CLIからの出力が2重にJSON化されている場合がある
                # parsed_dataが文字列の場合は、もう一度パースする
                if isinstance(parsed_data, str):
                    logger.info("Response is a JSON string, parsing again")
                    logger.info(f"String content sample: {parsed_data[:200]}")

                    try:
                        # まず通常のパースを試みる
                        parsed_data = json.loads(parsed_data)
                        logger.info(f"Second parse successful, type: {type(parsed_data)}")
                    except json.JSONDecodeError as e2:
                        logger.warning(f"Second parse failed: {e2}, trying with escaped control chars")

                        # エスケープされていない制御文字を修正してリトライ
                        try:
                            import re
                            # 実際の改行/タブ/キャリッジリターンをエスケープシーケンスに置換
                            # ただし、既にエスケープされている\\nは置換しない
                            cleaned_str = parsed_data.replace('\\n', '\x00')  # 一時的にマーク
                            cleaned_str = cleaned_str.replace('\n', '\\n')
                            cleaned_str = cleaned_str.replace('\r', '\\r')
                            cleaned_str = cleaned_str.replace('\t', '\\t')
                            cleaned_str = cleaned_str.replace('\x00', '\\n')  # 元に戻す

                            parsed_data = json.loads(cleaned_str)
                            logger.info(f"Second parse successful after escaping control chars, type: {type(parsed_data)}")
                        except json.JSONDecodeError as e3:
                            logger.error(f"Second parse failed even after escaping: {e3}")
                            # パース失敗時は文字列をそのまま使用
                            logger.warning("Using raw string as response data")
                            parsed_data = {"raw_text": parsed_data}

                logger.info(f"Final parsed_data keys: {parsed_data.keys() if isinstance(parsed_data, dict) else 'not a dict'}")

                # 構造化データとして返す
                return {
                    'success': True,
                    'data': parsed_data,
                    'session_id': result.get('session_id'),
                    'agent_type': result.get('agent_type'),
                    'is_mock': result.get('is_mock', False)
                }
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response: {e}")
                logger.error(f"Response text: {response_text[:500]}")

                # パース失敗時は元のテキストを返す
                return {
                    'success': True,
                    'data': {
                        'recommended_jobs': [],
                        'summary': 'レスポンスのパースに失敗しました',
                        'raw_response': response_text
                    },
                    'session_id': result.get('session_id'),
                    'agent_type': result.get('agent_type')
                }

        # エラー時はそのまま返す
        return result

    def evaluate_fit(
        self,
        user_id: str,
        candidate_id: str,
        job_id: str,
        detailed_analysis: bool = False
    ) -> Dict[str, Any]:
        """
        個別のマッチング評価

        Args:
            user_id: ユーザーID
            candidate_id: 候補者ID
            job_id: 求人ID
            detailed_analysis: 詳細分析フラグ

        Returns:
            マッチング評価
        """
        prompt = f"""
候補者ID: {candidate_id} と 求人ID: {job_id} の{"詳細" if detailed_analysis else "簡潔な"}マッチング分析を実行してください。

評価項目：
1. 必須要件の充足度
2. 歓迎要件の充足度
3. カルチャーフィット
4. 成長可能性
5. リスク要因
"""
        return self.invoke(user_id, prompt)


class InterviewerCopilotService(BaseAgentService):
    """面接官支援サービス"""

    def __init__(self):
        super().__init__("interviewer_copilot")

    def generate_interview_questions(
        self,
        user_id: str,
        job_role: str,
        interview_type: str = "general",
        difficulty: str = "medium",
        count: int = 5,
        job_context: Optional[Dict] = None,
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        面接質問を生成

        Args:
            user_id: ユーザーID
            job_role: 職種
            interview_type: 面接タイプ
            difficulty: 難易度
            count: 質問数
            job_context: 求人の詳細情報
            session_id: セッションID（会話履歴を保持）

        Returns:
            生成された質問リスト
        """
        # Job details for the prompt
        job_details = ""
        if job_context:
            job_details = f"""
[Job Details]
- Title: {job_context.get('title', job_role)}
- Description: {job_context.get('description', '')}
- Responsibilities: {job_context.get('responsibilities', '')}
- Qualifications: {job_context.get('qualifications', '')}
- Experience Level: {job_context.get('experience_level', '')}
"""

        prompt = f"""
You are an excellent interviewer. Generate {count} interview questions for a {interview_type} interview for the following job posting.

{job_details}

[Requirements]
- Difficulty: {difficulty}
- Number of questions: {count}
- Interview type: {interview_type}

[IMPORTANT INSTRUCTIONS]
1. Return ONLY valid JSON format
2. Do NOT use markdown code blocks (```json)
3. Do NOT include any explanatory text or preamble
4. You MUST respond in the following format:

{{
  "questions": [
    {{
      "id": 1,
      "question_text": "Please tell us about your work experience.",
      "question_type": "{interview_type}",
      "difficulty": "{difficulty}",
      "order": 1,
      "expected_answer": "Answer including specific experience and achievements",
      "evaluation_criteria": "Specificity, logic, communication skills"
    }},
    {{
      "id": 2,
      "question_text": "Second question...",
      "question_type": "{interview_type}",
      "difficulty": "{difficulty}",
      "order": 2,
      "expected_answer": "...",
      "evaluation_criteria": "..."
    }}
  ]
}}

[NOTES]
- Each question_text should be specific and easy for candidates to understand
- evaluation_criteria should clearly state the evaluation criteria
- Be careful to avoid JSON syntax errors (commas, brackets, quotes)
"""
        return self.invoke(user_id, prompt, context=job_context, session_id=session_id)

    def evaluate_answer(
        self,
        user_id: str,
        question: str,
        answer: str,
        job_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        回答を評価

        Args:
            user_id: ユーザーID
            question: 質問
            answer: 回答
            job_context: 求人コンテキスト

        Returns:
            評価結果
        """
        prompt = f"""
面接での回答を評価してください。

質問: {question}
回答: {answer}

評価基準：
1. 回答の完成度（1-10）
2. 具体性（1-10）
3. 関連性（1-10）
4. コミュニケーション（1-10）

強みと改善点を指摘してください。
"""
        return self.invoke(user_id, prompt, context=job_context)

    def evaluate_interview_session(
        self,
        user_id: str,
        session_id: str,
        qa_text: str,
        job_title: str
    ) -> Dict[str, Any]:
        """
        面接セッション全体を評価

        Args:
            user_id: ユーザーID
            session_id: セッションID
            qa_text: 質問と回答のペア（整形済み）
            job_title: 求人タイトル

        Returns:
            評価結果
        """
        prompt = f"""
{job_title}ポジションの面接が完了しました。以下の質問と回答を総合的に評価してください。

【質問と回答】
{qa_text}

【評価項目】
1. 技術力・専門性（1-10）
2. コミュニケーション能力（1-10）
3. 問題解決能力（1-10）
4. モチベーション・熱意（1-10）
5. カルチャーフィット（1-10）

【重要な指示】
応答は必ず以下のJSON形式のみで返してください。マークダウンのコードブロック（```json）や説明文は使用しないでください。

{{
  "evaluation_report": {{
    "overall_score": 7,
    "strengths": [
      "技術的な基礎知識が豊富である",
      "コミュニケーション能力が高い",
      "問題解決へのアプローチが論理的である"
    ],
    "areas_for_improvement": [
      "実務経験がやや不足している",
      "リーダーシップ経験を積む必要がある"
    ],
    "recommendation": "合格",
    "comment": "総合的なフィードバックをここに記載してください。候補者の強みと改善点、今後の成長可能性について詳細に説明してください。"
  }}
}}

【注意事項】
- overall_scoreは1-10の整数で評価してください
- strengthsとareas_for_improvementは配列形式で、それぞれ2-5個の項目を含めてください
- recommendationは「合格」「不合格」「保留」のいずれかを使用してください
- commentには200-500文字程度の詳細なフィードバックを記載してください
- JSON形式のみで応答し、他の文章は含めないでください
"""
        return self.invoke(user_id, prompt, session_id=session_id)


# サービスインスタンスのファクトリ関数
def get_agent_service(agent_type: str) -> Optional[BaseAgentService]:
    """
    指定されたタイプのエージェントサービスを取得

    Args:
        agent_type: エージェントタイプ

    Returns:
        エージェントサービスインスタンス
    """
    services = {
        'concierge': ConciergeService,
        'skill_parser': SkillParserService,
        'job_matcher': JobMatcherService,
        'interviewer_copilot': InterviewerCopilotService
    }

    service_class = services.get(agent_type)
    if service_class:
        return service_class()
    return None


# 便利な関数（APIビューから直接呼び出すため）
def chat_with_concierge(
    user_query: str,
    candidate_info: Optional[Dict[str, Any]] = None,
    user_id: str = "anonymous"
) -> str:
    """
    コンシェルジュと会話

    Args:
        user_query: ユーザーの質問
        candidate_info: 候補者情報（オプション）
        user_id: ユーザーID（デフォルト: "anonymous"）

    Returns:
        コンシェルジュの応答テキスト

    Raises:
        Exception: エラーが発生した場合
    """
    service = ConciergeService()
    result = service.assist_candidate(
        user_id=user_id,
        query=user_query,
        candidate_info=candidate_info
    )

    if not result.get('success'):
        error_msg = result.get('error', 'Unknown error')
        logger.error(f"Concierge service failed: {error_msg}")
        raise Exception(f"Concierge service error: {error_msg}")

    # 成功時は応答テキストを返す
    response_text = result.get('response', '')

    # AgentCoreからの応答がJSON形式の場合、resultフィールドを抽出
    try:
        parsed_response = json.loads(response_text)
        if isinstance(parsed_response, dict) and 'result' in parsed_response:
            logger.info("Extracted 'result' field from JSON response")
            return parsed_response['result']
    except (json.JSONDecodeError, TypeError):
        # JSONでない場合はそのまま返す
        pass

    return response_text
