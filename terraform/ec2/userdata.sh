#!/bin/bash
set -e

# Update system packages and install Docker
yum update -y
amazon-linux-extras install docker -y
service docker start
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install CodeDeploy Agent (for Amazon Linux 2 in ap-southeast-1)
yum install -y ruby wget
cd /home/ec2-user
wget https://aws-codedeploy-ap-southeast-1.s3.amazonaws.com/latest/install
chmod +x ./install
./install auto
service codedeploy-agent start

# Create Airflow working directories
mkdir -p /home/ec2-user/airflow/{dags,logs}

# Create the docker-compose file for Airflow scheduler
cat << 'EOF' > /home/ec2-user/airflow/docker-compose.yml
version: '3.8'

services:
  airflow-scheduler:
    image: ph_shoes_airflow_scheduler:latest
    container_name: airflow-scheduler
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__CORE__FERNET_KEY=YOUR_FERNET_KEY_HERE
      - AIRFLOW__CORE__LOAD_EXAMPLES=False
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
    command: ["airflow", "scheduler"]
EOF

# Replace the placeholder with an actual Fernet key
FERNET_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
sed -i "s/YOUR_FERNET_KEY_HERE/${FERNET_KEY}/g" /home/ec2-user/airflow/docker-compose.yml

# Set ownership so ec2-user manages the files
chown -R ec2-user:ec2-user /home/ec2-user/airflow

# Optionally initialize the Airflow database (you could also use CodeDeploy hooks for this)
echo "Initializing Airflow metadata database..."
docker run --rm ph_shoes_airflow_scheduler:latest airflow db init

# Start Docker Compose in detached mode (this starts the scheduler)
cd /home/ec2-user/airflow
docker-compose up -d

echo "Airflow scheduler container started."
