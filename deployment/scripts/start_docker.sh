#!/usr/bin/env bash
set -euxo pipefail

DEPLOYMENT_DIR=/home/ec2-user/deployment
AIRFLOW_DIR=/home/ec2-user/airflow

cd "$DEPLOYMENT_DIR"

# Load the image
docker load -i ph_shoes_airflow_scheduler.tar

# Run scheduler using airflow dir for volumes
docker run -d --name airflow-scheduler \
  -e PYTHONPATH=/opt/airflow \
  -v "$AIRFLOW_DIR/logs":/opt/airflow/logs \
  -v "$AIRFLOW_DIR/dags":/opt/airflow/dags \
  ph_shoes_airflow_scheduler:latest \
  bash -c "airflow db init && exec airflow scheduler"
