#!/usr/bin/env bash
set -euxo pipefail

DEPLOYMENT_DIR=/home/ec2-user/deployment
AIRFLOW_DIR=/home/ec2-user/airflow
BUCKET=ph-shoes-airflow-artifacts
ZIPKEY=deployment/deployment.zip

# Clean and prepare
rm -rf "$DEPLOYMENT_DIR"
mkdir -p "$DEPLOYMENT_DIR"
cd "$DEPLOYMENT_DIR"

# Download and unzip
aws s3 cp "s3://$BUCKET/$ZIPKEY" deployment.zip
unzip -o deployment.zip

# Extract docker image
find . -type f -name 'ph_shoes_airflow_scheduler.tar' -exec mv {} "$DEPLOYMENT_DIR"/ \; || true

# Prepare airflow directory and move dags/logs there
mkdir -p "$AIRFLOW_DIR/dags" "$AIRFLOW_DIR/logs"
chmod 777 "$AIRFLOW_DIR/dags" "$AIRFLOW_DIR/logs"
