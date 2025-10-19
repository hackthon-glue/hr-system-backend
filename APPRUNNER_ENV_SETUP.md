# App Runner 環境変数設定ガイド

## 方法1: AWS マネジメントコンソール（最も簡単）

1. **App Runnerコンソールを開く**
   ```
   https://console.aws.amazon.com/apprunner/home?region=ap-northeast-1
   ```

2. **サービスを選択** → **Configuration** タブ → **Edit**

3. **環境変数を追加**：

   | 変数名 | 値 |
   |--------|-----|
   | `SECRET_KEY` | `your-super-secret-key-min-50-chars` |
   | `DEBUG` | `False` |
   | `ALLOWED_HOSTS` | `<your-app-url>.ap-northeast-1.awsapprunner.com` |
   | `DB_NAME` | `hr_agent_db` |
   | `DB_USER` | `postgres` |
   | `DB_PASSWORD` | `postgres1005` |
   | `DB_HOST` | `aws-hackthon-deploy-db.cgopafft6i56.ap-northeast-1.rds.amazonaws.com` |
   | `DB_PORT` | `5432` |
   | `AWS_REGION` | `ap-northeast-1` |
   | `AWS_BEDROCK_AGENT_ID` | `HrAgent-uVxcle2LzN` |
   | `CORS_ALLOWED_ORIGINS` | `https://your-frontend.com` |
   | `LOG_LEVEL` | `INFO` |

4. **Save** → 自動で再デプロイが開始されます

---

## 方法2: AWS CLI（JSON使用）

### ステップ1: Service ARNを取得

```bash
aws apprunner list-services --region ap-northeast-1 --query "ServiceSummaryList[?ServiceName=='your-service-name'].ServiceArn" --output text
```

または：

```bash
aws apprunner list-services --region ap-northeast-1
```

### ステップ2: env-variables.jsonを編集

`env-variables.json`ファイルを開いて、以下の値を**本番用に変更**：

- `SECRET_KEY`: 強力なランダム文字列（50文字以上）
- `ALLOWED_HOSTS`: App RunnerのURL
- `CORS_ALLOWED_ORIGINS`: フロントエンドのURL

### ステップ3: 環境変数を設定

```bash
SERVICE_ARN="<your-service-arn>"

aws apprunner update-service \
  --service-arn "$SERVICE_ARN" \
  --region ap-northeast-1 \
  --source-configuration '{
    "CodeRepository": {
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      }
    }
  }' \
  --cli-input-json file://env-variables-update.json
```

**または、より簡単な方法**:

```bash
SERVICE_ARN="<your-service-arn>"

aws apprunner update-service \
  --service-arn "$SERVICE_ARN" \
  --region ap-northeast-1 \
  --instance-configuration file://env-variables.json
```

---

## 方法3: シェルスクリプト使用

### ステップ1: スクリプトに実行権限を付与

```bash
chmod +x set_apprunner_env.sh
```

### ステップ2: スクリプトを編集

`set_apprunner_env.sh`を開いて、本番用の値に変更：

```bash
SECRET_KEY="your-actual-secret-key"
ALLOWED_HOSTS="your-app.ap-northeast-1.awsapprunner.com"
CORS_ALLOWED_ORIGINS="https://your-frontend.com"
```

### ステップ3: 実行

```bash
./set_apprunner_env.sh arn:aws:apprunner:ap-northeast-1:123456789012:service/your-service/abc123
```

---

## 方法4: 個別に環境変数を追加（テスト用）

```bash
SERVICE_ARN="<your-service-arn>"

# 個別に追加
aws apprunner update-service \
  --service-arn "$SERVICE_ARN" \
  --region ap-northeast-1 \
  --source-configuration '{
    "CodeRepository": {
      "SourceCodeVersion": {"Type": "BRANCH", "Value": "main"}
    }
  }' \
  --instance-configuration '{
    "InstanceRoleArn": "",
    "Cpu": "1 vCPU",
    "Memory": "2 GB"
  }'
```

---

## 現在の環境変数を確認

```bash
SERVICE_ARN="<your-service-arn>"

aws apprunner describe-service \
  --service-arn "$SERVICE_ARN" \
  --region ap-northeast-1 \
  --query 'Service.SourceConfiguration.CodeRepository.CodeConfiguration.CodeConfigurationValues.RuntimeEnvironmentVariables'
```

---

## 🔐 重要: SECRET_KEYの生成

強力なSECRET_KEYを生成：

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

または：

```bash
openssl rand -base64 50
```

---

## 📝 注意事項

1. **DB_PASSWORD**: 本番環境では必ずセキュアな値に変更
2. **SECRET_KEY**: 開発用のキーは絶対に使用しない
3. **DEBUG**: 本番環境では必ず`False`
4. **ALLOWED_HOSTS**: App RunnerのURLを正確に指定
5. **CORS_ALLOWED_ORIGINS**: フロントエンドのURLを正確に指定
6. **AWS_PROFILE**: App Runnerでは不要（IAMロール使用）

---

## トラブルシューティング

### 環境変数が反映されない
- 設定後、自動的に再デプロイが開始されます（数分かかります）
- CloudWatch Logsで確認：
  ```bash
  aws logs tail /aws/apprunner/your-service/application --follow
  ```

### Service ARNが見つからない
```bash
aws apprunner list-services --region ap-northeast-1 --output table
```

### 権限エラー
App RunnerのIAMロールに以下の権限が必要：
- `bedrock:InvokeAgent`
- RDSへのVPCアクセス権限
