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