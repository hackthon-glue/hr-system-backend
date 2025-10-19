#!/bin/bash

# App Runner環境変数設定スクリプト
# 使い方: ./set_apprunner_env.sh <service-arn> <region>

SERVICE_ARN=$1
REGION=${2:-ap-northeast-1}

if [ -z "$SERVICE_ARN" ]; then
  echo "❌ Usage: $0 <service-arn> [region]"
  echo "Example: $0 arn:aws:apprunner:ap-northeast-1:123456789012:service/my-service/abc123 ap-northeast-1"
  exit 1
fi

echo "🚀 Setting environment variables for App Runner service..."
echo "Service ARN: $SERVICE_ARN"
echo "Region: $REGION"
echo ""

# ⚠️ 本番環境用の値に変更してください
SECRET_KEY="your-super-secret-key-change-this-to-strong-random-string-min-50-chars"
DEBUG="False"
ALLOWED_HOSTS="your-app.ap-northeast-1.awsapprunner.com"
CORS_ALLOWED_ORIGINS="https://your-frontend.com"

# データベース設定
DB_NAME="hr_agent_db"
DB_USER="postgres"
DB_PASSWORD="postgres1005"
DB_HOST="aws-hackthon-deploy-db.cgopafft6i56.ap-northeast-1.rds.amazonaws.com"
DB_PORT="5432"

# AWS設定
AWS_REGION="ap-northeast-1"
AWS_BEDROCK_AGENT_ID="HrAgent-uVxcle2LzN"

# ログレベル
LOG_LEVEL="INFO"

# AWS CLIコマンドを実行
aws apprunner update-service \
  --service-arn "$SERVICE_ARN" \
  --region "$REGION" \
  --source-configuration '{
    "CodeRepository": {
      "SourceCodeVersion": {
        "Type": "BRANCH",
        "Value": "main"
      },
      "CodeConfiguration": {
        "ConfigurationSource": "REPOSITORY"
      }
    }
  }' \
  --instance-configuration '{
    "Cpu": "1 vCPU",
    "Memory": "2 GB",
    "InstanceRoleArn": ""
  }' \
  --network-configuration '{
    "EgressConfiguration": {
      "EgressType": "DEFAULT"
    }
  }' \
  --observability-configuration '{
    "ObservabilityEnabled": true
  }' \
  --environment-variables \
    "SECRET_KEY=$SECRET_KEY" \
    "DEBUG=$DEBUG" \
    "ALLOWED_HOSTS=$ALLOWED_HOSTS" \
    "DB_NAME=$DB_NAME" \
    "DB_USER=$DB_USER" \
    "DB_PASSWORD=$DB_PASSWORD" \
    "DB_HOST=$DB_HOST" \
    "DB_PORT=$DB_PORT" \
    "AWS_REGION=$AWS_REGION" \
    "AWS_BEDROCK_AGENT_ID=$AWS_BEDROCK_AGENT_ID" \
    "CORS_ALLOWED_ORIGINS=$CORS_ALLOWED_ORIGINS" \
    "LOG_LEVEL=$LOG_LEVEL"

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ Environment variables updated successfully!"
  echo "⏳ Deployment in progress... Check App Runner console for status"
else
  echo ""
  echo "❌ Failed to update environment variables"
  exit 1
fi
