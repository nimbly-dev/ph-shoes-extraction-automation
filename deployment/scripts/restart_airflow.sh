#!/bin/bash
cd /home/ec2-user/airflow
docker-compose down
docker-compose up -d
