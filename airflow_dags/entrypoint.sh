#!/bin/bash
set -e

echo "Initializing Airflow DB..."
# Using db migrate instead of db init (as recommended)
airflow db migrate

echo "Creating default connections..."
airflow connections create-default-connections

echo "Creating admin user (if not already present)..."
# The '|| true' ensures that if the user already exists, the command doesn't fail
airflow users create \
  --username admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com \
  --password admin || true

echo "Starting Airflow..."
exec "$@"
