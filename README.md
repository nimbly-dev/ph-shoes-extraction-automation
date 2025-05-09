# PH Shoe Extractor Automation

Scrape well-known Shoes brand on PH Brand Sites
---

## 🧱 Project Structure

```bash
shoe-extractor-automation/
│
├── airflow_dags/             # Airflow DAGs and orchestration logic
│   ├── dags/                 # Python DAG files
│   ├── Dockerfile            # Airflow dev container
│   └── requirements.txt      # Airflow dependencies
│
├── lambda_extract/           # AWS Lambda scraping logic
│   ├── extractors/           # Brand-specific scrapers (Asics, Nike, etc.)
│   ├── lambda_handler.py     # Lambda entry point
│   ├── Dockerfile            # For local Lambda dev/testing
│   ├── test_runner.py        # Run extractors locally
│   └── requirements.txt      # Lambda runtime dependencies
│
├── glue_jobs/                # AWS Glue ETL jobs for data cleaning/transform
│   ├── clean_*.py            # PySpark Glue jobs
│   ├── Dockerfile            # Glue local test environment
│   └── glue_requirements.txt # Additional packages for Glue (optional)
│
├── scripts/                  # Utility scripts
│   └── package_lambda.sh     # Builds Lambda .zip package for deployment
│
├── terraform/                # Infrastructure as code definitions (Lambda, Glue, S3, etc.)
│   ├── main.tf
│   ├── lambda.tf
│   ├── glue.tf
│   ├── s3.tf
│   ├── variables.tf
│   └── outputs.tf
│
├── .github/                  # CI/CD workflows
│   └── workflows/
│       ├── deploy_lambda.yml
│       ├── deploy_airflow.yml
│       └── deploy_glue.yml
│
├── docker-compose.yml        # Compose file to spin up Airflow, Lambda dev, etc.
└── README.md


Services Users:

1. ph-shoes-terraform-user: Terraform user



Supported on Lambda Daily Extraction Automation:

1. Hoka
2. Nike
3. World Balance

Not Supported but present on Local Web Extractors

1. Asics
2. New Balance 
3. Adidas


sudo tail -F /var/log/aws/codedeploy-agent/codedeploy-agent.log


Clean codedeploy:

# 1) Stop the agent so it doesn’t fight you over files
sudo systemctl stop codedeploy-agent

# 2) Remove all archived revisions (old bundles + unpacked dirs)
sudo rm -rf /opt/codedeploy-agent/deployment-root/*

# 3) (Optional) Clear rotated logs if you need more room
sudo rm -rf /var/log/aws/codedeploy-agent/*

# 4) Restart agent
sudo systemctl start codedeploy-agent

.\deploy_airflow_local.ps1 -SkipUpload

docker rm -f airflow-scheduler 2>/dev/null || true

docker logs -f airflow-scheduler

docker exec -it airflow-scheduler airflow dags trigger ph_shoes_etl

docker exec -it airflow-scheduler airflow dags list

docker exec -it airflow-scheduler \
  airflow dags unpause ph_shoes_etl


Airflow Deployment Step

1. Build airflow_dags project using Docker, put it on .tar ball
2. Build deployment.zip, include .tar ball, and scripts, appspec.yml
3. Put to S3 Airflow Artifacts 
4. Provision EC2 Instances, wait for it to boot-up (Ensure that Old Instances is removed after new EC2 Startup)
5. Run Codedeploy


terraform-core: Contains provisioning modules for project e.g iAM for EC2, S3 Bucket for Artifacts, VPC Group connection
terraform-ec2-airflow: Contains EC2 Template where airflow code will be deployed.

terraform output redshift_admin_password

$ aws secretsmanager describe-secret \
   --secret-id prod/ph-shoes/redshift-master \
   --region ap-southeast-1 \
   --query 'ARN' \
   --output text