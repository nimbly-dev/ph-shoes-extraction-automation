#!/usr/bin/env bash
set -euxo pipefail

WORKDIR=/home/ec2-user/deployment
cd "$WORKDIR"

# load the image
docker load -i ph_shoes_airflow_scheduler.tar


# launch the scheduler in detached mode
docker run -d --name airflow-scheduler \
  -e PYTHONPATH=/opt/airflow \
  -v "$WORKDIR/logs":/opt/airflow/logs \
  ph_shoes_airflow_scheduler:latest \
  bash -c "airflow db init && exec airflow scheduler"