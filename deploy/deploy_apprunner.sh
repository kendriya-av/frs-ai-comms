#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# Deploy FRS AI Comms to AWS App Runner via ECR
#
# Prerequisites:
#   - AWS CLI configured (aws sso login --profile <profile>)
#   - Docker installed and running
#   - jq installed (brew install jq / apt install jq)
#
# Usage:
#   chmod +x deploy_apprunner.sh
#   ./deploy_apprunner.sh
# ─────────────────────────────────────────────────────────────────────────────

set -euo pipefail

# ── Config — edit these ───────────────────────────────────────────────────────
AWS_PROFILE="${AWS_PROFILE:-default}"
AWS_REGION="${AWS_REGION:-us-east-1}"
APP_NAME="frs-ai-comms"
ECR_REPO_NAME="frs-ai-comms"
APPRUNNER_SERVICE_NAME="frs-ai-comms"

# ── Derived values ────────────────────────────────────────────────────────────
ACCOUNT_ID=$(aws sts get-caller-identity --profile "$AWS_PROFILE" --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
IMAGE_TAG="latest"
FULL_IMAGE="${ECR_URI}:${IMAGE_TAG}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  FRS AI Comms — AWS App Runner Deployment"
echo "  Account : $ACCOUNT_ID"
echo "  Region  : $AWS_REGION"
echo "  Image   : $FULL_IMAGE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── Step 1: Create ECR repo if it doesn't exist ───────────────────────────────
echo ""
echo "▶ Step 1: Ensuring ECR repository exists..."
aws ecr describe-repositories \
    --repository-names "$ECR_REPO_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" > /dev/null 2>&1 || \
aws ecr create-repository \
    --repository-name "$ECR_REPO_NAME" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --image-scanning-configuration scanOnPush=true \
    --query 'repository.repositoryUri' \
    --output text
echo "  ✓ ECR repository ready: $ECR_URI"

# ── Step 2: Build Docker image ────────────────────────────────────────────────
echo ""
echo "▶ Step 2: Building Docker image..."
cd "$(dirname "$0")/.."
docker build -t "$APP_NAME:$IMAGE_TAG" .
echo "  ✓ Image built"

# ── Step 3: Push to ECR ───────────────────────────────────────────────────────
echo ""
echo "▶ Step 3: Pushing to ECR..."
aws ecr get-login-password \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" | \
docker login --username AWS --password-stdin \
    "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker tag "$APP_NAME:$IMAGE_TAG" "$FULL_IMAGE"
docker push "$FULL_IMAGE"
echo "  ✓ Image pushed to ECR"

# ── Step 4: Create/update App Runner service ──────────────────────────────────
echo ""
echo "▶ Step 4: Deploying to App Runner..."

# Check if service already exists
SERVICE_ARN=$(aws apprunner list-services \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query "ServiceSummaryList[?ServiceName=='${APPRUNNER_SERVICE_NAME}'].ServiceArn" \
    --output text 2>/dev/null || echo "")

# Load env vars from .env if present
ENV_VARS=""
if [ -f ".env" ]; then
    while IFS='=' read -r key value; do
        # Skip comments and empty lines
        [[ "$key" =~ ^#.*$ ]] && continue
        [[ -z "$key" ]] && continue
        [[ -z "$value" ]] && continue
        ENV_VARS="${ENV_VARS}{\"Name\":\"${key}\",\"Value\":\"${value}\"},"
    done < .env
    ENV_VARS="${ENV_VARS%,}"  # remove trailing comma
fi

if [ -z "$SERVICE_ARN" ]; then
    echo "  Creating new App Runner service..."

    # Create IAM role for App Runner to pull from ECR (if not exists)
    ROLE_NAME="AppRunnerECRAccessRole"
    ROLE_ARN=$(aws iam get-role --role-name "$ROLE_NAME" \
        --profile "$AWS_PROFILE" \
        --query 'Role.Arn' --output text 2>/dev/null || echo "")

    if [ -z "$ROLE_ARN" ]; then
        echo "  Creating IAM role for ECR access..."
        ROLE_ARN=$(aws iam create-role \
            --role-name "$ROLE_NAME" \
            --profile "$AWS_PROFILE" \
            --assume-role-policy-document '{
                "Version":"2012-10-17",
                "Statement":[{
                    "Effect":"Allow",
                    "Principal":{"Service":"build.apprunner.amazonaws.com"},
                    "Action":"sts:AssumeRole"
                }]
            }' \
            --query 'Role.Arn' --output text)
        aws iam attach-role-policy \
            --role-name "$ROLE_NAME" \
            --profile "$AWS_PROFILE" \
            --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
        echo "  ✓ IAM role created: $ROLE_ARN"
    fi

    # Build service config JSON
    CONFIG=$(cat <<EOF
{
    "ServiceName": "${APPRUNNER_SERVICE_NAME}",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "${FULL_IMAGE}",
            "ImageConfiguration": {
                "Port": "8050",
                "RuntimeEnvironmentVariables": {
                    "AWS_REGION": "${AWS_REGION}"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AuthenticationConfiguration": {
            "AccessRoleArn": "${ROLE_ARN}"
        },
        "AutoDeploymentsEnabled": true
    },
    "InstanceConfiguration": {
        "Cpu": "1 vCPU",
        "Memory": "2 GB"
    },
    "HealthCheckConfiguration": {
        "Protocol": "HTTP",
        "Path": "/",
        "Interval": 20,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 3
    }
}
EOF
)
    SERVICE_ARN=$(aws apprunner create-service \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --cli-input-json "$CONFIG" \
        --query 'Service.ServiceArn' \
        --output text)
    echo "  ✓ App Runner service created: $SERVICE_ARN"
else
    echo "  Updating existing App Runner service..."
    aws apprunner start-deployment \
        --service-arn "$SERVICE_ARN" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" > /dev/null
    echo "  ✓ Deployment triggered"
fi

# ── Step 5: Wait and get URL ──────────────────────────────────────────────────
echo ""
echo "▶ Step 5: Waiting for service to be running (this takes ~2 minutes)..."
for i in $(seq 1 24); do
    STATUS=$(aws apprunner describe-service \
        --service-arn "$SERVICE_ARN" \
        --region "$AWS_REGION" \
        --profile "$AWS_PROFILE" \
        --query 'Service.Status' \
        --output text 2>/dev/null || echo "UNKNOWN")
    echo "  Status: $STATUS (${i}/24)"
    if [ "$STATUS" = "RUNNING" ]; then
        break
    fi
    sleep 10
done

SERVICE_URL=$(aws apprunner describe-service \
    --service-arn "$SERVICE_ARN" \
    --region "$AWS_REGION" \
    --profile "$AWS_PROFILE" \
    --query 'Service.ServiceUrl' \
    --output text)

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Deployment complete!"
echo "  URL: https://${SERVICE_URL}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  Next: Set environment variables in App Runner console:"
echo "  https://console.aws.amazon.com/apprunner/home?region=${AWS_REGION}"
echo "  → Select service → Configuration → Environment variables"
echo "  → Add: AWS_PROFILE, BEDROCK_MODEL_ID, FRED_API_KEY, NEWS_API_KEY"
