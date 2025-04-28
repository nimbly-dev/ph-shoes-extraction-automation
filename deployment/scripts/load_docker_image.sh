#!/usr/bin/env bash
# deployment/scripts/load_docker_image.sh
set -euxo pipefail

AIRFLOWDIR=/home/ec2-user/airflow
BUCKET=ph-shoes-airflow-artifacts
ZIPKEY=deployment/deployment.zip

cd /home/ec2-user/deployment
docker load -i ph_shoes_airflow_scheduler.tar

docker-compose run --rm scheduler airflow db init