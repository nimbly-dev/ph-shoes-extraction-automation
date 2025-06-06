#!/bin/bash
set -euxo pipefail

AWS_REGION=${AWS_REGION}

# prepare directories…
mkdir -p /home/ec2-user/deployment /home/ec2-user/airflow/{dags,logs}
chown -R ec2-user:ec2-user /home/ec2-user

# install Docker & Compose…
yum update -y
amazon-linux-extras install docker -y
systemctl enable --now docker
usermod -aG docker ec2-user
curl -Lo /usr/local/bin/docker-compose \
  "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)"
chmod +x /usr/local/bin/docker-compose

# install CodeDeploy agent…
yum install -y ruby wget
cd /home/ec2-user
wget https://aws-codedeploy-${AWS_REGION}.s3.${AWS_REGION}.amazonaws.com/latest/install
chmod +x install
./install auto
systemctl enable --now codedeploy-agent

# install & start SSM Agent…
yum install -y amazon-ssm-agent
systemctl enable --now amazon-ssm-agent
