# Deployment Guide

## Option 1 — AWS App Runner (Recommended for demos)

Fully managed, no servers, HTTPS out of the box. ~2 min to deploy.

### Prerequisites
- Docker installed and running
- AWS CLI configured: `aws sso login --profile <your-profile>`
- Your profile has ECR + App Runner permissions

### Steps

```bash
cd frs_ai_comms

./deploy/deploy_apprunner.sh
```

The script will:
1. Create an ECR repository
2. Build and push the Docker image
3. Create an App Runner service
4. Output the public HTTPS URL

### Set environment variables after deploy
Go to **App Runner console → your service → Configuration → Environment variables** and add:

| Key | Value |
|---|---|
| `AWS_REGION` | `us-east-1` |
| `BEDROCK_MODEL_ID` | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `FRED_API_KEY` | your FRED key (optional) |
| `NEWS_API_KEY` | your NewsAPI key chmod +x deploy/deploy_apprunner.sh(optional) |

> **Note:** The app uses the EC2 instance metadata credentials when running on AWS — no `AWS_PROFILE` needed in the container. The IAM role attached to the App Runner service provides access to Comprehend and Bedrock.

### IAM role for App Runner
Attach `deploy/iam_policy.json` as an inline policy to the App Runner task role so it can call Comprehend and Bedrock.

---

## Option 2 — EC2 Instance

Good for full control, persistent storage, and running on a schedule.

### Launch an EC2 instance
- **AMI:** Amazon Linux 2023
- **Instance type:** `t3.medium` (2 vCPU, 4 GB RAM minimum)
- **Security group:** Allow inbound TCP 80 (HTTP) and 22 (SSH)
- **IAM role:** Attach a role with `deploy/iam_policy.json` permissions

### Deploy
```bash
# SSH into the instance
ssh -i your-key.pem ec2-user@<public-ip>

# Upload your code
scp -r frs_ai_comms/ ec2-user@<public-ip>:/opt/frs-ai-comms/

# Run the deploy script
chmod +x /opt/frs-ai-comms/frs_ai_comms/deploy/deploy_ec2.sh
/opt/frs-ai-comms/frs_ai_comms/deploy/deploy_ec2.sh
```

The script installs Python, creates a systemd service, and sets up nginx as a reverse proxy on port 80.

### Update after code changes
```bash
# On EC2
cd /opt/frs-ai-comms
git pull
sudo systemctl restart frs-ai-comms
```

---

## Option 3 — CodeBuild + App Runner (No local Docker needed)

Build the Docker image in AWS using CodeBuild — nothing to install locally except the AWS CLI.

### Prerequisites
- AWS CLI installed: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
- Logged in: `aws sso login --profile <your-profile>`
- Your profile has permissions for: ECR, CodeBuild, S3, IAM, App Runner

### Run the deploy script

```powershell
cd frs_ai_comms
.\deploy\deploy_codebuild.ps1
```

You can also pass parameters:
```powershell
.\deploy\deploy_codebuild.ps1 -AwsProfile "MyProfile" -AwsRegion "us-east-1"
```

### What the script does automatically
1. Gets your AWS account ID
2. Creates an ECR repository
3. Creates an S3 bucket and uploads your source code as a zip
4. Creates a CodeBuild project with the right IAM role
5. Starts the build — CodeBuild pulls the source, builds the Docker image, pushes to ECR
6. Creates IAM roles for App Runner (ECR access + Comprehend/Bedrock task role)
7. Creates an App Runner service pointing to the ECR image
8. Waits and outputs the public HTTPS URL

### Total time: ~8-10 minutes

### After deployment
The script reads your `.env` file and passes the values as App Runner environment variables automatically. Make sure your `.env` has:
```
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

---

## Credentials on AWS (no .env needed)

When running on AWS (App Runner, EC2, ECS), the app automatically uses the **IAM role** attached to the compute resource. You do **not** need `AWS_PROFILE` or static credentials.

The only keys you need to set as environment variables are:
- `AWS_REGION` — the region where Bedrock and Comprehend are enabled
- `BEDROCK_MODEL_ID` — the Claude model to use
- `FRED_API_KEY` — optional, for FRED economic data
- `NEWS_API_KEY` — optional, for NewsAPI news articles

---

## Cost estimate (App Runner)

| Resource | Cost |
|---|---|
| App Runner (1 vCPU, 2 GB, ~8 hrs/day) | ~$15–25/month |
| Amazon Comprehend (per 100 chars) | ~$0.0001 |
| Amazon Bedrock (Claude 3 Sonnet, per 1K tokens) | ~$0.003 input / $0.015 output |
| ECR storage | ~$0.10/GB/month |

For a hackathon demo, total cost is typically under $5.
