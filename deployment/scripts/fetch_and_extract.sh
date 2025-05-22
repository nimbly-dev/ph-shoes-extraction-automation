#!/usr/bin/env bash
set -euxo pipefail

DEPLOYMENT_DIR=/home/ec2-user/deployment
AIRFLOW_DIR=/home/ec2-user/airflow
BUCKET=ph-shoes-airflow-artifacts
ZIPKEY=deployment/deployment.zip

# 1) Clean and prepare
rm -rf "$DEPLOYMENT_DIR"
mkdir -p "$DEPLOYMENT_DIR"
cd "$DEPLOYMENT_DIR"

# 2) Download and unzip
aws s3 cp "s3://$BUCKET/$ZIPKEY" deployment.zip
unzip -o deployment.zip

# 3) Extract scheduler Docker image
find . -type f -name 'ph_shoes_airflow_scheduler.tar' -exec mv {} "$DEPLOYMENT_DIR"/ \; || true

# 4) Extract & deploy DAGs
if [ -f dags.tar.gz ]; then
  tar xzf dags.tar.gz
  mkdir -p "$AIRFLOW_DIR/dags"
  cp -r dags/* "$AIRFLOW_DIR/dags"/
  chown -R ec2-user:ec2-user "$AIRFLOW_DIR/dags"
fi

# 5) Ensure logs directory exists
mkdir -p "$AIRFLOW_DIR/logs"
chmod 777 "$AIRFLOW_DIR/logs"
