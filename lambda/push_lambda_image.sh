#!/bin/bash
set -e

# Resolve project root
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

# Load .env file from /lambda
if [ -f "$PROJECT_ROOT/lambda/.env" ]; then
  echo "📦 Loading environment variables from lambda/.env"
  export $(grep -v '^#' "$PROJECT_ROOT/lambda/.env" | xargs)
else
  echo "❌ .env file not found at $PROJECT_ROOT/lambda"
  exit 1
fi

# Docker/ECR setup
AWS_REGION="ap-southeast-1"
IMAGE_NAME="ph-shoes-lambda-shared"            
REPO_NAME="${IMAGE_NAME}-repo"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_URI="${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"

echo "🧱 Building Docker image..."
docker build -t ${IMAGE_NAME} ./lambda

echo "🔐 Logging in to ECR..."
aws ecr get-login-password --region ${AWS_REGION} \
  | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "🏷 Tagging image..."
docker tag ${IMAGE_NAME}:latest ${ECR_URI}:latest

echo "📤 Pushing image to ECR..."
docker push ${ECR_URI}:latest

echo "🔎 Fetching pushed image digest..."
IMAGE_DIGEST=$(aws ecr describe-images \
  --repository-name "${REPO_NAME}" \
  --region "${AWS_REGION}" \
  --profile terraform \
  --query "imageDetails[?imageTags && contains(imageTags, 'latest')].imageDigest" \
  --output text)
  
echo "✅ Image pushed successfully"
echo "🔗 ECR URI (tagged): ${ECR_URI}:latest"
echo "🔗 ECR URI (digest): ${ECR_URI}@${IMAGE_DIGEST}"
