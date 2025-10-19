# AWS Bedrock AgentCore統合ドキュメント

## 概要

Django バックエンドとAWS Bedrock AgentCoreの統合実装。
AgentCoreは独立したサービスとして動作し、Djangoから必要に応じて呼び出します。

## アーキテクチャ

```
┌─────────────────┐
│  Django Backend │
│  (API Server)   │
└────────┬────────┘
         │ boto3
         │ invoke_agent()
         ▼
┌─────────────────────────┐
│  AWS Bedrock AgentCore  │
│  (独立デプロイ)          │
│  - agents/ ディレクトリ  │
│  - 4つのコアエージェント│
└─────────────────────────┘
```

## 実装ファイル

### 1. AgentCoreクライアント層

#### `backend/services/agent_client.py`
- **AgentCoreClient**: boto3でBedrockと通信
- **AgentSession**: セッション管理
- 機能:
  - `invoke_agent()`: エージェント呼び出し
  - `invoke_with_retry()`: リトライ機能付き呼び出し
  - ストリーミングレスポンス処理
  - モックモード（開発用）

#### `backend/services/hr_agent_services.py`
- **BaseAgentService**: 全エージェントの基底クラス
- 4つのコアサービス:
  1. **ConciergeService** - 候補者コンシェルジュ
  2. **SkillParserService** - スキル解析
  3. **JobMatcherService** - 求人マッチング
  4. **InterviewerCopilotService** - 面接官支援

### 2. APIエンドポイント統合

#### 候補者API (`backend/candidates/views.py`)

**CandidateViewSet**に追加したアクション:

1. **POST `/api/candidates/{id}/parse_skills/`**
   - 履歴書テキストからスキルを抽出
   - Request: `{"resume_text": "..."}`
   - AgentCore: SkillParserService

2. **POST `/api/candidates/{id}/career_advice/`**
   - キャリアアドバイスを提供
   - Request: `{"question": "..."}`
   - AgentCore: ConciergeService

3. **POST `/api/candidates/{id}/match_jobs/`**
   - 求人マッチング
   - 候補者プロフィールと求人リストを自動取得
   - AgentCore: JobMatcherService

**InterviewViewSet**に追加したアクション:

4. **POST `/api/candidates/interviews/{id}/evaluate_answer/`**
   - 面接回答を評価
   - Request: `{"question": "...", "answer": "..."}`
   - AgentCore: InterviewerCopilotService

#### 求人API (`backend/jobs/views.py`)

**JobViewSet**に追加したアクション:

1. **POST `/api/jobs/{id}/generate_interview_questions/`**
   - 面接質問を生成
   - Request: `{"interview_type": "technical", "difficulty": "medium", "count": 5}`
   - AgentCore: InterviewerCopilotService

## 設定

### 環境変数 (`.env`)

```bash
# AWS Bedrock設定
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=ap-northeast-1
AWS_BEDROCK_AGENT_ID=your_agent_id
```

### Django設定 (`backend/hr_agent_system/settings.py`)

```python
# AWS Settings (for AgentCore integration)
AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = config('AWS_SECRET_ACCESS_KEY', default='')
AWS_REGION = config('AWS_REGION', default='ap-northeast-1')
AWS_BEDROCK_AGENT_ID = config('AWS_BEDROCK_AGENT_ID', default='')
```

## 使用方法

### 開発環境（モックモード）

AWS設定が未設定の場合、自動的にモックモードで動作します。

```bash
# サーバー起動
cd backend
source .venv/bin/activate
python manage.py runserver
```

### 本番環境（AWS Bedrock使用）

1. AWS Bedrock AgentCoreを設定
2. 環境変数を設定
3. サーバー起動

```bash
# .env ファイルを作成
cat > backend/.env << EOF
AWS_ACCESS_KEY_ID=your_actual_key
AWS_SECRET_ACCESS_KEY=your_actual_secret
AWS_REGION=ap-northeast-1
AWS_BEDROCK_AGENT_ID=your_agent_id
EOF

# サーバー起動
cd backend
source .venv/bin/activate
python manage.py runserver
```

## APIリクエスト例

### 1. スキル解析

```bash
curl -X POST http://localhost:8000/api/candidates/1/parse_skills/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "resume_text": "Python、Django、AWS、Docker、Kubernetesの経験が5年あります"
  }'
```

レスポンス:
```json
{
  "message": "スキル解析が完了しました。",
  "result": "抽出されたスキル情報...",
  "session_id": "user123-skill_parser-a1b2c3d4",
  "is_mock": true
}
```

### 2. キャリアアドバイス

```bash
curl -X POST http://localhost:8000/api/candidates/1/career_advice/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "バックエンドエンジニアとしてキャリアアップするには？"
  }'
```

### 3. 求人マッチング

```bash
curl -X POST http://localhost:8000/api/candidates/1/match_jobs/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
```

### 4. 面接質問生成

```bash
curl -X POST http://localhost:8000/api/jobs/1/generate_interview_questions/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "interview_type": "technical",
    "difficulty": "medium",
    "count": 5
  }'
```

### 5. 面接回答評価

```bash
curl -X POST http://localhost:8000/api/candidates/interviews/1/evaluate_answer/ \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Djangoでの経験を教えてください",
    "answer": "5年間Djangoで..."
  }'
```

## エラーハンドリング

### モックモード

AWS設定が未設定の場合:
- `AgentCoreClient.is_available()` が `False` を返す
- 自動的にモックレスポンスを返す
- レスポンスに `"is_mock": true` フラグが含まれる

### 本番環境

- **リトライ機能**: 最大3回自動リトライ（指数バックオフ）
- **タイムアウト処理**: boto3のデフォルトタイムアウト設定を使用
- **エラーログ**: すべてのエラーをDjangoログに記録

## テスト

```bash
# Django チェック
cd backend
source .venv/bin/activate
python manage.py check

# サーバー起動確認
python manage.py runserver

# ヘルスチェック
curl http://localhost:8000/health/
```

## Swagger API ドキュメント

サーバー起動後、以下にアクセス:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

新しいエージェント呼び出しエンドポイントがすべて表示されます。

## 次のステップ

### AWS Bedrock設定（Phase 4.1 - 4.5）

1. **Bedrock AgentCore設定**
   - IAMロール作成
   - エージェント登録
   - エイリアス作成

2. **Knowledge Base構築**
   - S3バケット作成
   - ドキュメントアップロード
   - RAG設定

3. **Memory設定**
   - DynamoDBテーブル作成
   - セッション永続化

4. **Guardrails設定**
   - バイアス検出ポリシー
   - 禁止ワードフィルター

## トラブルシューティング

### ImportError: No module named 'services'

Python pathの問題。以下を確認:
```python
# backend/manage.py または wsgi.py に追加
import sys
sys.path.insert(0, os.path.dirname(__file__))
```

### AgentCore接続エラー

1. AWS認証情報を確認
2. リージョン設定を確認（ap-northeast-1）
3. AgentIDが正しいか確認
4. IAMロール権限を確認

### モックレスポンスのみ返される

- `.env`ファイルが正しく読み込まれているか確認
- `AWS_BEDROCK_AGENT_ID`が設定されているか確認

## ライセンス

MIT License
