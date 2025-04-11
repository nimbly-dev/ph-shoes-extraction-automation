#!/bin/bash
set -e
TARBALL="/home/ec2-user/deployment/ph_shoes_airflow_scheduler.tar"
if [ -f "$TARBALL" ]; then
  echo "Loading Docker image from tarball..."
  docker load -i "$TARBALL"
else
  echo "ERROR: Tarball not found at ${TARBALL}"
  exit 1
fi
