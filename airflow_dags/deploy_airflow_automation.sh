#!/bin/bash
set -e

# --- Resolve Project Root and Load Environment Variables ---
PROJECT_ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$PROJECT_ROOT"

ENV_FILE="$PROJECT_ROOT/airflow_dags/.env"
if [ -f "$ENV_FILE" ]; then
  echo "📦 Loading environment variables from $ENV_FILE"
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "❌ .env file not found at $ENV_FILE"
  exit 1
fi

# --- Configuration Variables ---
IMAGE_NAME=${IMAGE_NAME:-"ph_shoes_airflow_scheduler:latest"}
TARBALL_NAME=${TARBALL_NAME:-"ph_shoes_airflow_scheduler.tar"}
AWS_REGION=${AWS_REGION:-"ap-southeast-1"}
SECRET_ID="ph-shoes-ssh-private-key"
APP_DEPLOY_ARTIFACT="deployment.zip"

echo "Using IMAGE_NAME: ${IMAGE_NAME}"
echo "Using TARBALL_NAME: ${TARBALL_NAME}"
echo "Using AWS_REGION: ${AWS_REGION}"
echo "Using SECRET_ID: ${SECRET_ID}"

# --- Build and Save Docker Image ---
cd "$PROJECT_ROOT/airflow_dags"

if [ ! -f "Dockerfile" ]; then
  echo "❌ Dockerfile not found in $PROJECT_ROOT/airflow_dags"
  exit 1
fi

echo "🧱 Building Docker image..."
docker build -t ${IMAGE_NAME} .

echo "💾 Saving Docker image to tarball..."
docker save -o ${TARBALL_NAME} ${IMAGE_NAME}

# --- Check if zip command exists, and install if not ---
if ! command -v zip &>/dev/null; then
  echo "zip command not found. Installing zip..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get update && sudo apt-get install -y zip
  elif command -v yum &>/dev/null; then
    sudo yum install -y zip
  elif command -v pacman &>/dev/null; then
    pacman -Sy --noconfirm zip
  elif command -v choco &>/dev/null; then
    choco install zip -y
  else
    echo "Error: No recognized package manager found; please install zip manually."
    exit 1
  fi
else
  echo "zip command is installed."
fi

# --- Package Deployment Artifact ---
cd "$PROJECT_ROOT/deployment"
echo "📦 Packaging deployment artifact..."
if [[ "$(uname)" == *"MINGW"* ]]; then
  echo "Detected Windows environment. Using PowerShell Compress-Archive..."

  # Create a temporary folder for packaging
  TEMP_DIR=$(mktemp -d)

  # Copy required files into the temporary folder
  cp appspec.yaml "$TEMP_DIR/"
  cp -r scripts "$TEMP_DIR/"
  cp "$PROJECT_ROOT/airflow_dags/${TARBALL_NAME}" "$TEMP_DIR/"

  # Convert Unix-style paths to Windows-style for the compress step
  WIN_TEMP_DIR=$(cygpath -w "$TEMP_DIR")
  WIN_DEST=$(cygpath -w "$PROJECT_ROOT/deployment/${APP_DEPLOY_ARTIFACT}")

  # Use PowerShell Compress-Archive to create the ZIP artifact
  powershell.exe -Command "Compress-Archive -Path '${WIN_TEMP_DIR}\*' -DestinationPath '${WIN_DEST}' -Force"

  # Clean up the temporary folder
  rm -rf "$TEMP_DIR"
else
  zip -j ${APP_DEPLOY_ARTIFACT} appspec.yaml scripts/* "$PROJECT_ROOT/airflow_dags/${TARBALL_NAME}"
fi
# --- Upload Artifact to S3 ---
S3_BUCKET="ph-shoes-airflow-artifacts"
echo "Uploading artifact to S3 bucket ${S3_BUCKET}..."

# Unix‑style path for reference
FILE_UNIX="${PROJECT_ROOT}/deployment/${APP_DEPLOY_ARTIFACT}"

if [[ "$(uname)" == *"MINGW"* ]]; then
  # Convert to mixed Windows path
  WIN_FILE=$(cygpath -m "${FILE_UNIX}")
  echo "PowerShell will upload: ${WIN_FILE}"

  # Invoke AWS CLI from inside PowerShell so that the Windows path is used literally
  powershell.exe -NoProfile -Command \
    "aws s3 cp '${WIN_FILE}' 's3://${S3_BUCKET}/deployment/${APP_DEPLOY_ARTIFACT}' --region ${AWS_REGION}"

else
  aws s3 cp "${FILE_UNIX}" "s3://${S3_BUCKET}/deployment/${APP_DEPLOY_ARTIFACT}" --region ${AWS_REGION}
fi


# --- Trigger CodeDeploy Deployment ---
APP_NAME="ph-shoes-airflow-codedeploy-app"
DEPLOY_GROUP="ph-shoes-airflow-deployment-group"

echo "Triggering CodeDeploy deployment..."
aws deploy create-deployment \
  --application-name ${APP_NAME} \
  --deployment-group-name ${DEPLOY_GROUP} \
  --s3-location bucket=${S3_BUCKET},bundleType=zip,key=deployment/${APP_DEPLOY_ARTIFACT} \
  --region ${AWS_REGION}

echo "✅ CodeDeploy deployment triggered successfully!"
