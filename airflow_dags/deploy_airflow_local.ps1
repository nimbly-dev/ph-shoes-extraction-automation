param(
    [switch]$SkipUpload
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 0) Sanity checks
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw '❌ Docker CLI not found. Install & start Docker Desktop.'
}
try { docker info | Out-Null } catch { throw '❌ Docker daemon not running.' }
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    throw '❌ AWS CLI not found. Install AWS CLI v2.'
}
try { aws sts get-caller-identity --region ap-southeast-1 | Out-Null } catch {
    throw '❌ AWS CLI cannot talk to AWS. Check credentials + network.'
}

# 1) Determine project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if ((Split-Path $scriptDir -Leaf).ToLower() -eq 'airflow_dags') {
    $projectRoot = Split-Path -Parent $scriptDir
} else { $projectRoot = $scriptDir }
Write-Host "ℹ️ Project root: $projectRoot"

# 2) Load .env
$envFile = Join-Path $projectRoot 'airflow_dags\.env'
if (-not (Test-Path $envFile)) { throw "❌ .env not found at $envFile" }
Get-Content $envFile |
  Where-Object { $_ -and -not $_.StartsWith('#') } |
  ForEach-Object {
    $parts = $_.Split('=',2); $k=$parts[0].Trim(); $v=$parts[1].Trim("'",'"')
    [Environment]::SetEnvironmentVariable($k,$v)
    Write-Host "   -> $k=$v"
  }

# 3) Defaults
if (-not $env:IMAGE_NAME)          { $env:IMAGE_NAME          = 'ph_shoes_airflow_scheduler:latest' }
if (-not $env:TARBALL_NAME)        { $env:TARBALL_NAME        = 'ph_shoes_airflow_scheduler.tar' }
if (-not $env:APP_DEPLOY_ARTIFACT) { $env:APP_DEPLOY_ARTIFACT = 'deployment.zip' }
if (-not $env:AWS_REGION)          { $env:AWS_REGION          = 'ap-southeast-1' }

Write-Host "`n🔧 Using:" `
  "`n   IMAGE_NAME = $env:IMAGE_NAME" `
  "`n   TARBALL    = $env:TARBALL_NAME" `
  "`n   ZIP_ARTIFACT = $env:APP_DEPLOY_ARTIFACT" `
  "`n   AWS_REGION = $env:AWS_REGION"

# 4) Build & save Docker image
Write-Host "`n🧱 Building Docker image..."
Push-Location (Join-Path $projectRoot 'airflow_dags')
docker build -t $env:IMAGE_NAME . | Write-Host
docker save -o (Join-Path $projectRoot $env:TARBALL_NAME) $env:IMAGE_NAME | Write-Host
Pop-Location

# 5) Package deployment.zip
Write-Host "`n📦 Packaging deployment artifact..."
$tempDir = Join-Path $env:TEMP ([guid]::NewGuid())
New-Item -ItemType Directory -Path $tempDir | Out-Null

Copy-Item (Join-Path $projectRoot 'deployment\appspec.yml') `
          -Destination (Join-Path $tempDir 'appspec.yml')
Copy-Item (Join-Path $projectRoot 'deployment\scripts') -Destination $tempDir -Recurse
Copy-Item (Join-Path $projectRoot $env:TARBALL_NAME) -Destination $tempDir

$zipPath = Join-Path $projectRoot "deployment\$($env:APP_DEPLOY_ARTIFACT)"
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Push-Location $tempDir
Compress-Archive -Path * -DestinationPath $zipPath -Force
Pop-Location
Remove-Item $tempDir -Recurse
Write-Host "✅ Created $zipPath"

$bucket = 'ph-shoes-airflow-artifacts'

if (-not $SkipUpload) {
  # 6) Upload to S3
  $key    = "deployment/$($env:APP_DEPLOY_ARTIFACT)"
  Write-Host "`n⬆ Uploading to s3://$bucket/$key"
  aws s3 rm "s3://$bucket/$key" --region $env:AWS_REGION | Out-Null
  aws s3 cp $zipPath "s3://$bucket/$key" --region $env:AWS_REGION | Write-Host


  Write-Host "`n✅ Deployment triggered successfully!"
} else {
  Write-Host "`n⚠️ Skipping S3 upload trigger due to -SkipUpload."
}

# 7) Trigger CodeDeploy
$app   = 'ph-shoes-airflow-codedeploy-app'
$group = 'ph-shoes-airflow-deployment-group'
$s3loc = "bucket=$bucket,bundleType=zip,key=deployment/$($env:APP_DEPLOY_ARTIFACT)"

Write-Host "`n🎯 Creating CodeDeploy deployment..."
aws deploy create-deployment `
--application-name $app `
--deployment-group-name $group `
--s3-location $s3loc `
--region $env:AWS_REGION | Write-Host