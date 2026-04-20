# ─────────────────────────────────────────────────────────────────────────────
# Deploy FRS AI Comms to AWS App Runner using CodeBuild (no local Docker needed)
# Compatible with Windows PowerShell 5.1+
#
# Usage (from the frs_ai_comms folder):
#   cd D:\Anitha.Vaideeswaran\genai\frs_ai_comms
#   .\deploy\deploy_codebuild.ps1 -AwsProfile "AWSAdministratorAccess-477239358762" -AwsRegion "us-east-1"
# ─────────────────────────────────────────────────────────────────────────────

param(
    [string]$AwsProfile   = "default",
    [string]$AwsRegion    = "us-east-1",
    [string]$AppName      = "frs-ai-comms",
    [string]$S3BucketName = ""
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  FRS AI Comms - AWS App Runner Deploy (via CodeBuild)" -ForegroundColor Cyan
Write-Host "  Profile : $AwsProfile" -ForegroundColor Cyan
Write-Host "  Region  : $AwsRegion" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# ── Helper functions ──────────────────────────────────────────────────────────

function Run-Aws {
    param([string[]]$CliArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = aws @CliArgs --profile $AwsProfile --region $AwsRegion --output json 2>&1
    $ErrorActionPreference = $prev
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI failed for: $CliArgs"
    }
    $jsonStr = ($output | Where-Object { $_ -is [string] }) -join ""
    return $jsonStr | ConvertFrom-Json
}

function Run-AwsText {
    param([string[]]$CliArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $output = aws @CliArgs --profile $AwsProfile --region $AwsRegion --output text 2>&1
    $ErrorActionPreference = $prev
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI failed for: $CliArgs"
    }
    return ($output | Where-Object { $_ -is [string] }) -join "" | ForEach-Object { $_.Trim() }
}

function Resource-Exists {
    param([string[]]$CliArgs)
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $null = aws @CliArgs --profile $AwsProfile --region $AwsRegion --output text 2>&1
    $ErrorActionPreference = $prev
    return $LASTEXITCODE -eq 0
}

# ── Step 1: Get account ID ────────────────────────────────────────────────────
Write-Host "`n[1/10] Getting AWS account ID..." -ForegroundColor Yellow
$AccountId = Run-AwsText @("sts", "get-caller-identity", "--query", "Account")
$EcrUri    = "$AccountId.dkr.ecr.$AwsRegion.amazonaws.com/$AppName"
Write-Host "  Account : $AccountId"
Write-Host "  ECR URI : $EcrUri"

# ── Step 2: Create ECR repository ────────────────────────────────────────────
Write-Host "`n[2/10] Ensuring ECR repository exists..." -ForegroundColor Yellow
$ecrExists = Resource-Exists @("ecr", "describe-repositories", "--repository-names", $AppName)
if ($ecrExists) {
    Write-Host "  ECR repository already exists"
} else {
    Run-Aws @("ecr", "create-repository", "--repository-name", $AppName,
              "--image-scanning-configuration", "scanOnPush=true") | Out-Null
    Write-Host "  ECR repository created: $EcrUri"
}

# ── Step 3: Create S3 bucket ──────────────────────────────────────────────────
Write-Host "`n[3/10] Setting up S3 bucket..." -ForegroundColor Yellow
if (-not $S3BucketName) {
    $S3BucketName = "$AppName-source-$AccountId"
}
$s3Exists = Resource-Exists @("s3api", "head-bucket", "--bucket", $S3BucketName)
if ($s3Exists) {
    Write-Host "  S3 bucket already exists: $S3BucketName"
} else {
    if ($AwsRegion -eq "us-east-1") {
        aws s3api create-bucket --bucket $S3BucketName --profile $AwsProfile --region $AwsRegion | Out-Null
    } else {
        aws s3api create-bucket --bucket $S3BucketName --profile $AwsProfile --region $AwsRegion `
            --create-bucket-configuration "LocationConstraint=$AwsRegion" | Out-Null
    }
    Write-Host "  S3 bucket created: $S3BucketName"
}

# ── Step 4: Zip and upload source code ───────────────────────────────────────
Write-Host "`n[4/10] Zipping and uploading source code..." -ForegroundColor Yellow
$ZipPath   = "$env:TEMP\frs-ai-comms-source.zip"
$SourceDir = Split-Path -Parent $PSScriptRoot

if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "$SourceDir\*" -DestinationPath $ZipPath -Force

aws s3 cp $ZipPath "s3://$S3BucketName/source.zip" --profile $AwsProfile | Out-Null
Write-Host "  Uploaded to s3://$S3BucketName/source.zip"

# ── Step 5: Create CodeBuild IAM role ────────────────────────────────────────
Write-Host "`n[5/10] Setting up CodeBuild IAM role..." -ForegroundColor Yellow
$CbRoleName = "CodeBuildFrsAiCommsRole"
$cbRoleExists = Resource-Exists @("iam", "get-role", "--role-name", $CbRoleName)
if ($cbRoleExists) {
    $CbRoleArn = Run-AwsText @("iam", "get-role", "--role-name", $CbRoleName, "--query", "Role.Arn")
    Write-Host "  CodeBuild IAM role already exists"
} else {
    $TrustPolicy = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"codebuild.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    $TrustFile   = "$env:TEMP\cb-trust.json"
    [System.IO.File]::WriteAllText($TrustFile, $TrustPolicy)

    $CbRoleArn = Run-AwsText @("iam", "create-role", "--role-name", $CbRoleName,
                               "--assume-role-policy-document", "file://$TrustFile",
                               "--query", "Role.Arn")

    $Policies = @(
        "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser",
        "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess",
        "arn:aws:iam::aws:policy/CloudWatchLogsFullAccess"
    )
    foreach ($Policy in $Policies) {
        aws iam attach-role-policy --role-name $CbRoleName --policy-arn $Policy --profile $AwsProfile | Out-Null
    }
    Write-Host "  CodeBuild IAM role created: $CbRoleArn"
    Write-Host "  Waiting 10s for role propagation..."
    Start-Sleep -Seconds 10
}

# ── Step 6: Create CodeBuild project ─────────────────────────────────────────
Write-Host "`n[6/10] Creating CodeBuild project..." -ForegroundColor Yellow
$ProjectName  = "$AppName-build"
$BuildspecPath = "$PSScriptRoot\buildspec.yml"
$BuildspecContent = (Get-Content $BuildspecPath -Raw).Replace('"', '\"').Replace("`r`n", "\n").Replace("`n", "\n")

$ProjectJson = @"
{
  "name": "$ProjectName",
  "description": "Build FRS AI Comms Docker image",
  "source": {
    "type": "S3",
    "location": "$S3BucketName/source.zip"
  },
  "artifacts": { "type": "NO_ARTIFACTS" },
  "environment": {
    "type": "LINUX_CONTAINER",
    "image": "aws/codebuild/standard:7.0",
    "computeType": "BUILD_GENERAL1_SMALL",
    "privilegedMode": true,
    "environmentVariables": [
      { "name": "ECR_URI",            "value": "$EcrUri",     "type": "PLAINTEXT" },
      { "name": "ECR_REPO_NAME",      "value": "$AppName",    "type": "PLAINTEXT" },
      { "name": "AWS_DEFAULT_REGION", "value": "$AwsRegion",  "type": "PLAINTEXT" }
    ]
  },
  "serviceRole": "$CbRoleArn",
  "logsConfig": {
    "cloudWatchLogs": { "status": "ENABLED", "groupName": "/codebuild/$ProjectName" }
  }
}
"@

$ProjectFile = "$env:TEMP\cb-project.json"
[System.IO.File]::WriteAllText($ProjectFile, $ProjectJson)

$cbProjectExists = Resource-Exists @("codebuild", "batch-get-projects", "--names", $ProjectName,
                                      "--query", "projects[0].name")
if ($cbProjectExists) {
    aws codebuild update-project --cli-input-json "file://$ProjectFile" `
        --profile $AwsProfile --region $AwsRegion | Out-Null
    Write-Host "  CodeBuild project updated"
} else {
    aws codebuild create-project --cli-input-json "file://$ProjectFile" `
        --profile $AwsProfile --region $AwsRegion | Out-Null
    Write-Host "  CodeBuild project created: $ProjectName"
}

# ── Step 7: Start build ───────────────────────────────────────────────────────
Write-Host "`n[7/10] Starting CodeBuild build (takes ~3-5 min)..." -ForegroundColor Yellow
$BuildId = Run-AwsText @("codebuild", "start-build", "--project-name", $ProjectName,
                          "--query", "build.id")
Write-Host "  Build ID: $BuildId"

$BuildStatus = ""
for ($i = 1; $i -le 40; $i++) {
    Start-Sleep -Seconds 15
    $BuildStatus = Run-AwsText @("codebuild", "batch-get-builds", "--ids", $BuildId,
                                  "--query", "builds[0].buildStatus")
    Write-Host "  [$i/40] $BuildStatus"
    if ($BuildStatus -eq "SUCCEEDED") { break }
    if ($BuildStatus -in @("FAILED", "FAULT", "STOPPED", "TIMED_OUT")) {
        Write-Host "  Build failed. Check logs:" -ForegroundColor Red
        Write-Host "  https://console.aws.amazon.com/codesuite/codebuild/projects/$ProjectName" -ForegroundColor Yellow
        exit 1
    }
}

if ($BuildStatus -ne "SUCCEEDED") {
    Write-Host "  Build timed out. Check CodeBuild console." -ForegroundColor Red
    exit 1
}
Write-Host "  Image pushed to ECR successfully"

# ── Step 8: App Runner ECR access role ───────────────────────────────────────
Write-Host "`n[8/10] Setting up App Runner IAM roles..." -ForegroundColor Yellow
$EcrRoleName = "AppRunnerECRAccessRole"
$ecrRoleExists = Resource-Exists @("iam", "get-role", "--role-name", $EcrRoleName)
if ($ecrRoleExists) {
    $EcrRoleArn = Run-AwsText @("iam", "get-role", "--role-name", $EcrRoleName, "--query", "Role.Arn")
    Write-Host "  ECR access role already exists"
} else {
    $EcrTrust    = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"build.apprunner.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    $EcrTrustFile = "$env:TEMP\ecr-trust.json"
    [System.IO.File]::WriteAllText($EcrTrustFile, $EcrTrust)
    $EcrRoleArn = Run-AwsText @("iam", "create-role", "--role-name", $EcrRoleName,
                                "--assume-role-policy-document", "file://$EcrTrustFile",
                                "--query", "Role.Arn")
    aws iam attach-role-policy --role-name $EcrRoleName --profile $AwsProfile `
        --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess" | Out-Null
    Write-Host "  ECR access role created"
    Start-Sleep -Seconds 10
}

# App Runner task role (Comprehend + Bedrock)
$TaskRoleName = "AppRunnerFrsAiCommsTaskRole"
$taskRoleExists = Resource-Exists @("iam", "get-role", "--role-name", $TaskRoleName)
if ($taskRoleExists) {
    $TaskRoleArn = Run-AwsText @("iam", "get-role", "--role-name", $TaskRoleName, "--query", "Role.Arn")
    Write-Host "  Task role already exists"
} else {
    $TaskTrust    = '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"tasks.apprunner.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
    $TaskTrustFile = "$env:TEMP\task-trust.json"
    [System.IO.File]::WriteAllText($TaskTrustFile, $TaskTrust)
    $TaskRoleArn = Run-AwsText @("iam", "create-role", "--role-name", $TaskRoleName,
                                 "--assume-role-policy-document", "file://$TaskTrustFile",
                                 "--query", "Role.Arn")
    $InlinePolicy = Get-Content "$PSScriptRoot\iam_policy.json" -Raw
    $InlinePolicyFile = "$env:TEMP\inline-policy.json"
    [System.IO.File]::WriteAllText($InlinePolicyFile, $InlinePolicy)
    aws iam put-role-policy --role-name $TaskRoleName --policy-name "ComprehendBedrock" `
        --policy-document "file://$InlinePolicyFile" --profile $AwsProfile | Out-Null
    Write-Host "  Task role created with Comprehend + Bedrock permissions"
    Start-Sleep -Seconds 10
}

# ── Step 9: Read env vars from .env ──────────────────────────────────────────
Write-Host "`n[9/10] Deploying to App Runner..." -ForegroundColor Yellow
$EnvMap = @{}
$EnvMap["AWS_REGION"] = $AwsRegion
$EnvFile = Join-Path (Split-Path -Parent $PSScriptRoot) ".env"
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line -match "^([^=]+)=(.+)$") {
            $EnvMap[$Matches[1].Trim()] = $Matches[2].Trim()
        }
    }
    Write-Host "  Loaded env vars from .env"
} else {
    Write-Host "  No .env file found - only AWS_REGION will be set"
}

# Build the RuntimeEnvironmentVariables JSON block as "KEY": "VALUE" pairs
$EnvPairs = @()
foreach ($key in $EnvMap.Keys) {
    $val = $EnvMap[$key]
    $EnvPairs += "        `"$key`": `"$val`""
}
$EnvBlock = $EnvPairs -join ",`n"

# ── Step 9b: Create/update App Runner service ─────────────────────────────────
$ServiceName = $AppName

# Write service config to a temp file (avoids here-string parsing issues)
$ServiceJsonContent = @(
    '{',
    "  `"ServiceName`": `"$ServiceName`",",
    '  "SourceConfiguration": {',
    '    "ImageRepository": {',
    "      `"ImageIdentifier`": `"${EcrUri}:latest`",",
    '      "ImageConfiguration": {',
    '        "Port": "8050",',
    '        "RuntimeEnvironmentVariables": {',
    $EnvBlock,
    '        }',
    '      },',
    '      "ImageRepositoryType": "ECR"',
    '    },',
    "    `"AuthenticationConfiguration`": { `"AccessRoleArn`": `"$EcrRoleArn`" },",
    '    "AutoDeploymentsEnabled": true',
    '  },',
    '  "InstanceConfiguration": {',
    '    "Cpu": "1 vCPU",',
    '    "Memory": "2 GB",',
    "    `"InstanceRoleArn`": `"$TaskRoleArn`"",
    '  },',
    '  "HealthCheckConfiguration": {',
    '    "Protocol": "HTTP",',
    '    "Path": "/",',
    '    "Interval": 20,',
    '    "Timeout": 5,',
    '    "HealthyThreshold": 1,',
    '    "UnhealthyThreshold": 3',
    '  }',
    '}'
) -join "`n"

$ServiceFile = "$env:TEMP\apprunner-service.json"
[System.IO.File]::WriteAllText($ServiceFile, $ServiceJsonContent)

# Check if service already exists
$ServiceArn = ""
$allServices = aws apprunner list-services --profile $AwsProfile --region $AwsRegion --output json 2>&1
if ($LASTEXITCODE -eq 0) {
    $parsed = ($allServices | Out-String) | ConvertFrom-Json
    $existing = $parsed.ServiceSummaryList | Where-Object { $_.ServiceName -eq $ServiceName }
    if ($existing) { $ServiceArn = $existing.ServiceArn }
}

if ($ServiceArn) {
    Write-Host "  Triggering redeployment of existing service..."
    aws apprunner start-deployment --service-arn $ServiceArn `
        --profile $AwsProfile --region $AwsRegion | Out-Null
} else {
    Write-Host "  Creating new App Runner service..."
    $ServiceArn = Run-AwsText @("apprunner", "create-service",
                                "--cli-input-json", "file://$ServiceFile",
                                "--query", "Service.ServiceArn")
    Write-Host "  Service ARN: $ServiceArn"
}

# ── Step 10: Wait for RUNNING ─────────────────────────────────────────────────
Write-Host "`n[10/10] Waiting for App Runner service to be RUNNING..." -ForegroundColor Yellow
$SvcStatus = ""
for ($i = 1; $i -le 24; $i++) {
    Start-Sleep -Seconds 15
    $SvcStatus = Run-AwsText @("apprunner", "describe-service",
                               "--service-arn", $ServiceArn,
                               "--query", "Service.Status")
    Write-Host "  [$i/24] $SvcStatus"
    if ($SvcStatus -eq "RUNNING") { break }
}

$ServiceUrl = Run-AwsText @("apprunner", "describe-service",
                            "--service-arn", $ServiceArn,
                            "--query", "Service.ServiceUrl")

Write-Host ""
Write-Host "================================================================" -ForegroundColor Green
Write-Host "  Deployment complete!" -ForegroundColor Green
Write-Host "  URL: https://$ServiceUrl" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  CodeBuild logs:" -ForegroundColor Cyan
Write-Host "  https://console.aws.amazon.com/codesuite/codebuild/projects/$ProjectName" -ForegroundColor Cyan
Write-Host "  App Runner console:" -ForegroundColor Cyan
Write-Host "  https://console.aws.amazon.com/apprunner/home?region=$AwsRegion" -ForegroundColor Cyan
