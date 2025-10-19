# HR Agent System API Documentation

## Overview

HR採用支援システムのバックエンドAPIドキュメント。

## Architecture

### Apps

1. **authz** - 認証・認可
2. **candidates** - 候補者管理
3. **jobs** - 求人管理
4. **agents** - AIエージェント
5. **audit** - 監査・コンプライアンス

## Models

### Candidates App

#### Skill (スキルマスター)
- スキル情報の管理
- カテゴリ: プログラミング、フレームワーク、データベース、クラウド、ツール、ソフトスキル、言語、その他

#### Candidate (候補者)
- 基本情報: 生年月日、性別、国籍、住所
- 職務情報: 現職、経験年数
- ステータス: アクティブ、非アクティブ、採用済み、辞退
- ドキュメント: 履歴書、ポートフォリオURL、LinkedIn、GitHub

#### CandidateProfile (候補者プロフィール)
- 自己紹介、キャリア目標
- スキル概要（技術・ソフト）
- 希望条件: 勤務形態、勤務地、リモートワーク
- 言語能力: 日本語、英語、その他
- 資格・認定、受賞歴、論文・執筆
- AI分析結果

#### CandidateSkill (候補者スキル)
- スキルと習熟度の関連付け
- 習熟度: 初級、中級、上級、エキスパート
- 経験年数、最終使用日

#### Education (学歴)
- 学校名、学位、専攻
- 開始日・終了日
- GPA

#### WorkExperience (職歴)
- 会社名、役職、雇用形態
- 職務内容、実績、使用技術
- チーム規模

#### Application (応募)
- 候補者と求人の関連付け
- ステータス: 下書き、応募済み、書類選考中、面接中、内定、承諾、不合格、辞退
- マッチングスコア
- AI推薦コメント
- 選考メモ、面接回数
- 内定情報

#### Interview (面接)
- 面接種類: 電話、オンライン、対面、技術面接、人事面接、最終面接
- 評価スコア: 技術、コミュニケーション、カルチャーフィット、総合
- フィードバック、強み、弱み

### Jobs App

#### Job (求人)
- 基本情報: タイトル、求人コード、部署、勤務地
- 雇用形態: 正社員、契約社員、パートタイム、インターン、派遣
- 経験レベル: 新卒・未経験、ジュニア、ミドル、シニア、リード・マネージャー
- 職務内容、応募資格
- 待遇: 年収範囲、福利厚生
- ステータス: 下書き、公開中、一時停止、募集終了、採用完了

#### JobRequirement (求人要件)
- 要件タイプ: 必須、歓迎、あれば尚可
- カテゴリ、説明、優先度

#### JobSkill (求人スキル)
- 求人に必要なスキル
- 要求レベル: 必須、歓迎
- 最低習熟度、最低経験年数
- 重み（マッチング計算用）

#### MatchingResult (マッチング結果)
- 総合スコア、スキルマッチスコア、経験マッチスコア、学歴マッチスコア、カルチャーフィットスコア
- マッチしたスキル、不足スキル、追加スキル
- AI分析サマリー、推薦レベル

#### SavedJob (保存済み求人)
- 候補者が保存した求人

#### JobView (求人閲覧履歴)
- 求人の閲覧履歴追跡

### Agents App

#### AgentSession (エージェントセッション)
- セッション種類: 求人検索、応募サポート、面接準備、キャリア相談、スキル評価、マッチング、一般
- AWS Bedrock連携情報
- メッセージ数、トークン数
- エラー情報

#### AgentConversation (エージェント会話)
- 役割: ユーザー、エージェント、システム
- メッセージタイプ: テキスト、提案、質問、回答、アクション、エラー
- トークン使用量、応答時間
- 参照求人・候補者
- ユーザーフィードバック

#### AgentMemory (エージェント記憶)
- 記憶タイプ: ユーザー設定、スキル、キャリア目標、求人希望、対話パターン、フィードバック、コンテキスト
- 重要度、信頼度
- 有効期限
- アクセス追跡

#### AgentAction (エージェントアクション)
- アクションタイプ: 求人検索、求人応募、求人保存、マッチング作成、プロフィール更新、面接予約、通知送信、ドキュメント生成、履歴書分析、アドバイス提供
- 入力データ、出力データ
- 実行時間

#### AgentFeedback (エージェントフィードバック)
- フィードバックタイプ: セッション全体、個別メッセージ、アクション、一般
- 評価: 非常に悪い〜非常に良い (1-5)
- 詳細評価: 正確性、有用性、応答速度
- フォローアップ管理

### Audit App

#### AuditLog (監査ログ)
- アクションタイプ: 作成、閲覧、更新、削除、ログイン、ログアウト、エクスポート、インポート、承認、却下、送信、ダウンロード
- リソース情報
- 変更内容（変更前・変更後）
- リクエスト・レスポンス情報
- 重要度、不審なアクティビティフラグ

#### BiasReport (バイアスレポート)
- バイアスタイプ: 性別、年齢、国籍、学歴、地域、名前、経験年数、その他
- 重要度: 低、中、高、重大
- ステータス: 未対応、確認中、対応済み、却下、誤検知
- 証拠データ、信頼度スコア
- AI分析、推奨アクション
- 対応履歴

#### DataAccessLog (個人情報アクセスログ)
- アクセスタイプ: 閲覧、エクスポート、ダウンロード、印刷、共有
- アクセスフィールド
- コンプライアンス情報（GDPR準拠）

#### ComplianceCheck (コンプライアンスチェック)
- チェックタイプ: GDPR、機会均等、データ保持、同意、透明性、バイアス検出、プライバシー
- ステータス: 未実施、実施中、合格、不合格、警告
- 発見事項、推奨事項
- コンプライアンススコア
- 是正措置

#### SystemMetrics (システムメトリクス)
- メトリクスタイプ: API呼び出し、エージェントセッション、マッチング、応募、ユーザーアクション、エラー、パフォーマンス
- メトリクス値、単位
- ディメンション

## API Endpoints

### Candidates

- `GET /api/candidates/skills/` - スキル一覧
- `POST /api/candidates/skills/` - スキル作成
- `GET /api/candidates/skills/{id}/` - スキル詳細
- `GET /api/candidates/skills/categories/` - スキルカテゴリ一覧

- `GET /api/candidates/candidates/` - 候補者一覧
- `POST /api/candidates/candidates/` - 候補者作成
- `GET /api/candidates/candidates/{id}/` - 候補者詳細
- `GET /api/candidates/candidates/me/` - 現在のユーザーの候補者情報
- `GET /api/candidates/candidates/{id}/profile/` - 候補者プロフィール詳細
- `POST /api/candidates/candidates/{id}/update_profile/` - プロフィール更新
- `GET /api/candidates/candidates/{id}/skills/` - 候補者スキル一覧
- `POST /api/candidates/candidates/{id}/add_skill/` - スキル追加
- `GET /api/candidates/candidates/{id}/educations/` - 学歴一覧
- `POST /api/candidates/candidates/{id}/add_education/` - 学歴追加
- `GET /api/candidates/candidates/{id}/work_experiences/` - 職歴一覧
- `POST /api/candidates/candidates/{id}/add_work_experience/` - 職歴追加

- `GET /api/candidates/applications/` - 応募一覧
- `POST /api/candidates/applications/` - 応募作成
- `GET /api/candidates/applications/{id}/` - 応募詳細
- `GET /api/candidates/applications/my_applications/` - 自分の応募一覧
- `POST /api/candidates/applications/{id}/update_status/` - 応募ステータス更新
- `GET /api/candidates/applications/{id}/interviews/` - 応募の面接一覧

- `GET /api/candidates/interviews/` - 面接一覧
- `POST /api/candidates/interviews/` - 面接作成
- `GET /api/candidates/interviews/{id}/` - 面接詳細
- `GET /api/candidates/interviews/upcoming/` - 今後の面接一覧
- `POST /api/candidates/interviews/{id}/submit_feedback/` - 面接フィードバック提出

### Jobs

- `GET /api/jobs/jobs/` - 求人一覧
- `POST /api/jobs/jobs/` - 求人作成
- `GET /api/jobs/jobs/{id}/` - 求人詳細
- `PUT /api/jobs/jobs/{id}/` - 求人更新
- `DELETE /api/jobs/jobs/{id}/` - 求人削除
- `POST /api/jobs/jobs/{id}/track_view/` - 求人閲覧を記録

- `GET /api/jobs/matching-results/` - マッチング結果一覧
- `POST /api/jobs/matching-results/` - マッチング結果作成
- `GET /api/jobs/matching-results/{id}/` - マッチング結果詳細
- `GET /api/jobs/matching-results/top_matches/` - トップマッチング結果

- `GET /api/jobs/saved-jobs/` - 保存済み求人一覧
- `POST /api/jobs/saved-jobs/` - 求人を保存
- `DELETE /api/jobs/saved-jobs/{id}/` - 保存済み求人削除

- `GET /api/jobs/job-views/` - 求人閲覧履歴

## Middleware

### AuditLogMiddleware
全てのHTTPリクエストを記録し、監査証跡を作成
- 除外パス: /admin/jsi18n/, /static/, /media/, /favicon.ico
- 除外メソッド: OPTIONS
- 記録内容: ユーザー情報、アクション、リソース、リクエスト・レスポンス情報、レスポンス時間

### DataAccessMiddleware
個人情報へのアクセスを記録
- 対象エンドポイント: /api/candidates/, /api/applications/, /api/interviews/
- GETリクエストのみ記録

## Services

### BedrockAgentService
AWS Bedrock Agent統合サービス
- `create_session()` - エージェントセッション作成
- `send_message()` - メッセージ送信
- `end_session()` - セッション終了
- `save_memory()` - ユーザー記憶保存
- `get_memories()` - ユーザー記憶取得
- `create_action()` - アクション作成
- `complete_action()` - アクション完了
- `fail_action()` - アクション失敗

### MatchingService
候補者と求人のマッチングサービス
- `calculate_matching_score()` - マッチングスコア計算
  - スキルマッチスコア (重み: 50%)
  - 経験マッチスコア (重み: 30%)
  - 学歴マッチスコア (重み: 20%)

## Permissions

### 役割ベースアクセス制御

- **candidate** (候補者)
  - 自分の情報のみ閲覧・編集
  - 公開中の求人閲覧
  - 求人への応募
  - 自分の応募・面接情報閲覧

- **recruiter** (採用担当者)
  - 担当求人の管理
  - 担当応募者の管理
  - マッチング結果閲覧

- **interviewer** (面接官)
  - 担当面接の閲覧・評価

- **admin** (管理者)
  - 全データへのアクセス

## Setup

### 環境変数

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=hr_agent_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# AWS
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=ap-northeast-1
AWS_BEDROCK_AGENT_ID=your-agent-id

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# JWT
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
```

### データベースマイグレーション

```bash
python manage.py makemigrations
python manage.py migrate
```

### スーパーユーザー作成

```bash
python manage.py createsuperuser
```

### サーバー起動

```bash
python manage.py runserver
```

## API Documentation

アクセス:
- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## Health Check

http://localhost:8000/health/

## Features

### 監査機能
- 全APIリクエストの記録
- 変更履歴の追跡
- 不審なアクティビティの検出
- 個人情報アクセスログ

### バイアス検出
- AI分析による潜在的バイアスの検出
- バイアスレポート生成
- 対応追跡

### コンプライアンス
- GDPR準拠
- データ保持ポリシー
- 同意管理
- コンプライアンスチェック

### AIエージェント
- AWS Bedrock統合
- 会話履歴管理
- 長期記憶（ユーザー設定、キャリア目標など）
- アクション追跡

### マッチング
- スキルベースマッチング
- 経験レベルマッチング
- 学歴マッチング
- AIによる推薦
