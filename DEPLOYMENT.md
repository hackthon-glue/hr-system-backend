# AWS App Runner Deployment Guide

## 📋 Pre-Deployment Checklist

### 1. Database Setup (Required)

**Create RDS PostgreSQL Instance:**
```bash
# Use AWS Console or CLI
# Recommended settings:
# - Engine: PostgreSQL 15+
# - Instance: db.t3.micro (for development)
# - Storage: 20GB
# - Public access: No
# - VPC: Same as App Runner
```

### 2. Environment Variables Configuration

Set these in App Runner Console under **Configuration → Environment Variables**:

#### Django Core Settings
```
SECRET_KEY=<generate-strong-random-key>
DEBUG=False
ALLOWED_HOSTS=<your-apprunner-url>.ap-northeast-1.awsapprunner.com
```

#### Database Settings (RDS PostgreSQL)
```
DB_NAME=hr_agent_db
DB_USER=postgres
DB_PASSWORD=<your-secure-password>
DB_HOST=<rds-endpoint>.ap-northeast-1.rds.amazonaws.com
DB_PORT=5432
```

#### AWS Bedrock Settings
```
AWS_REGION=ap-northeast-1
AWS_BEDROCK_AGENT_ID=HrAgent-uVxcle2LzN
```

#### CORS Settings
```
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,https://www.your-frontend-domain.com
```

#### Optional Settings
```
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440
LOG_LEVEL=INFO
```

### 3. IAM Role Configuration

App Runner needs permissions to access:
- **AWS Bedrock** - For AI agent functionality
- **RDS** - Database access (through VPC connector)
- **CloudWatch Logs** - Logging

**Required IAM Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeAgent",
        "bedrock:Retrieve"
      ],
      "Resource": "*"
    }
  ]
}
```

### 4. VPC Connector (If using RDS)

Create VPC Connector for App Runner:
- Select VPC where RDS is located
- Choose private subnets
- Configure security group to allow outbound to RDS

## 🚀 Deployment Steps

### Option 1: Deploy from GitHub

1. **Connect GitHub Repository**
   - Go to AWS App Runner Console
   - Create service → Source: GitHub
   - Authorize and select repository

2. **Configure Build**
   - Runtime: Python 3
   - Build command: Use `apprunner.yaml`

3. **Configure Service**
   - Port: 8000
   - Environment variables: Add all from section 2
   - Instance: 1 vCPU, 2 GB RAM (minimum)

4. **Configure Networking** (if using RDS)
   - Enable VPC connector
   - Select VPC connector created earlier

5. **Deploy**

### Option 2: Deploy from ECR (Docker)

If you prefer containerization, create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations and start server
CMD python manage.py migrate --noinput && \
    gunicorn hr_agent_system.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -

EXPOSE 8000
```

## 📝 Post-Deployment Tasks

### 1. Create Superuser

Connect to your App Runner instance and create an admin user:

```bash
# This needs to be done via AWS Systems Manager Session Manager
# or by adding a custom management command that runs on first deploy

# For now, you can create superuser data using the create_superuser.py script
# during the post-build phase or via Django admin after initial setup
```

### 2. Load Initial Data

```bash
# If you need to load sample data:
python manage.py loaddata initial_data.json
```

### 3. Test the Deployment

```bash
# Health check
curl https://<your-app>.ap-northeast-1.awsapprunner.com/admin/

# API test
curl https://<your-app>.ap-northeast-1.awsapprunner.com/api/jobs/
```

## 🔍 Monitoring & Logs

### CloudWatch Logs
App Runner automatically sends logs to CloudWatch:
- Application logs: Stdout/stderr
- Access logs: Gunicorn access logs

### Health Checks
App Runner performs automatic health checks on `/`

To customize health check endpoint, add to Django:
```python
# urls.py
path('health/', lambda request: JsonResponse({'status': 'healthy'}))
```

## 🛠 Troubleshooting

### Common Issues

**1. Database Connection Timeout**
- Check VPC connector configuration
- Verify security group allows traffic from App Runner
- Ensure RDS is in the same region

**2. Static Files Not Loading**
- Run `collectstatic` in post-build (already in apprunner.yaml)
- Consider using S3 for static files in production

**3. Migration Errors**
- Check database credentials
- Ensure RDS is accessible from App Runner
- Check CloudWatch logs for detailed errors

**4. Environment Variables Not Working**
- Verify all required variables are set in App Runner console
- Check for typos in variable names
- Restart service after adding new variables

## 📊 Scaling Configuration

App Runner auto-scales based on:
- CPU utilization
- Memory usage
- Request count

Configure in App Runner Console:
- **Min instances**: 1
- **Max instances**: 10
- **Concurrency**: 100 (requests per instance)

## 💰 Cost Optimization

- Use `db.t3.micro` for development
- Set auto-pause for development environments
- Use RDS Single-AZ for non-production
- Monitor CloudWatch metrics to optimize instance size

## 🔐 Security Best Practices

1. ✅ Never commit `.env` file
2. ✅ Use strong SECRET_KEY (at least 50 characters)
3. ✅ Set DEBUG=False in production
4. ✅ Configure ALLOWED_HOSTS with specific domains
5. ✅ Use HTTPS only (App Runner provides SSL automatically)
6. ✅ Rotate database passwords regularly
7. ✅ Enable RDS encryption at rest
8. ✅ Use IAM roles instead of hardcoded AWS credentials

## 📞 Support

For issues related to:
- **App Runner**: AWS Support
- **Application**: Check CloudWatch Logs
- **Database**: Check RDS metrics and logs
