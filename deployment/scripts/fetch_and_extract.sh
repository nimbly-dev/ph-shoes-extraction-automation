#!/usr/bin/env bash
set -euxo pipefail

DEPLOYMENT_DIR=/home/ec2-user/deployment
AIRFLOW_DIR=/home/ec2-user/airflow
BUCKET=ph-shoes-airflow-artifacts
ZIPKEY=deployment/deployment.zip

rm -rf "$DEPLOYMENT_DIR"
mkdir -p "$DEPLOYMENT_DIR"
cd "$DEPLOYMENT_DIR"

aws s3 cp "s3://$BUCKET/$ZIPKEY" deployment.zip
unzip -o deployment.zip
find . -type f -name 'ph_shoes_airflow_scheduler.tar' -exec mv {} "$DEPLOYMENT_DIR"/ \; || true

if [ -f dags.tar.gz ]; then
  tar xzf dags.tar.gz
  mkdir -p "$AIRFLOW_DIR/dags"
  cp -r dags/* "$AIRFLOW_DIR/dags"/
  chown -R ec2-user:ec2-user "$AIRFLOW_DIR/dags"
fi

mkdir -p "$AIRFLOW_DIR/logs"
chmod 777 "$AIRFLOW_DIR/logs"
