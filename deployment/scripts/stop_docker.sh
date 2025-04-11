#!/bin/bash
set -e
echo "Stopping and removing any existing Airflow scheduler container..."
docker stop airflow-scheduler || true
docker rm airflow-scheduler || true
