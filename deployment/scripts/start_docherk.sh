#!/bin/bash
set -e
echo "Starting Airflow scheduler container..."
# You may adjust ports and container parameters as needed.
docker run -d --name airflow-scheduler \
  -p 8080:8080 \
  ph_shoes_airflow_scheduler:latest
echo "Airflow scheduler started successfully."
