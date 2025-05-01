#!/usr/bin/env bash
set -euxo pipefail

WORKDIR=/home/ec2-user/deployment
BUCKET=ph-shoes-airflow-artifacts
ZIPKEY=deployment/deployment.zip

# clean & unpack into WORKDIR
rm -rf "$WORKDIR"
mkdir -p "$WORKDIR"
cd "$WORKDIR"
aws s3 cp "s3://$BUCKET/$ZIPKEY" deployment.zip
unzip -o deployment.zip

find . -type f -name 'ph_shoes_airflow_scheduler.tar' -exec mv {} "$WORKDIR"/ \; || true

# make sure host-mount dirs exist and are writable
mkdir -p "$WORKDIR/dags" "$WORKDIR/logs"
chmod 777 "$WORKDIR/dags" "$WORKDIR/logs"
