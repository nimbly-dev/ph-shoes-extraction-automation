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



Placeholder texts:

Terraform will perform the following actions:

  # module.s3_data_lake.aws_s3_bucket.data_lake will be created
  + resource "aws_s3_bucket" "data_lake" {
      + acceleration_status         = (known after apply)
      + acl                         = (known after apply)
      + arn                         = (known after apply)
      + bucket                      = "ph-shoes-data-lake"
      + bucket_domain_name          = (known after apply)
      + bucket_prefix               = (known after apply)
      + bucket_regional_domain_name = (known after apply)
      + force_destroy               = false
      + hosted_zone_id              = (known after apply)
      + id                          = (known after apply)
      + object_lock_enabled         = (known after apply)
      + policy                      = (known after apply)
      + region                      = (known after apply)
      + request_payer               = (known after apply)
      + tags                        = {
          + "Application" = "ph-shoes-scrapper-project"
          + "Environment" = "dev"
        }
      + tags_all                    = {
          + "Application" = "ph-shoes-scrapper-project"
          + "Environment" = "dev"
        }
      + website_domain              = (known after apply)
      + website_endpoint            = (known after apply)
    }

  # module.s3_data_lake.aws_s3_bucket_lifecycle_configuration.raw_expiry will be created
  + resource "aws_s3_bucket_lifecycle_configuration" "raw_expiry" {
      + bucket                                 = (known after apply)
      + expected_bucket_owner                  = (known after apply)
      + id                                     = (known after apply)
      + transition_default_minimum_object_size = "all_storage_classes_128K"

      + rule {
          + id     = "expire-raw-after-30-days"
          + prefix = (known after apply)
          + status = "Enabled"

          + expiration {
              + days                         = 30
              + expired_object_delete_marker = (known after apply)
            }

          + filter {
              + object_size_greater_than = (known after apply)
              + object_size_less_than    = (known after apply)
              + prefix                   = "raw/"
            }

          + noncurrent_version_expiration {
              + newer_noncurrent_versions = (known after apply)
              + noncurrent_days           = 7
            }
        }
    }

  # module.s3_data_lake.aws_s3_bucket_versioning.data_lake will be created
  + resource "aws_s3_bucket_versioning" "data_lake" {
      + bucket = (known after apply)
      + id     = (known after apply)

      + versioning_configuration {
          + mfa_delete = (known after apply)
          + status     = "Enabled"
        }
    }

  # module.s3_data_lake.aws_s3_object.raw_prefix_marker will be created
  + resource "aws_s3_object" "raw_prefix_marker" {
      + acl                    = (known after apply)
      + arn                    = (known after apply)
      + bucket                 = (known after apply)
      + bucket_key_enabled     = (known after apply)
      + checksum_crc32         = (known after apply)
      + checksum_crc32c        = (known after apply)
      + checksum_crc64nvme     = (known after apply)
      + checksum_sha1          = (known after apply)
      + checksum_sha256        = (known after apply)
      + content_type           = (known after apply)
      + etag                   = (known after apply)
      + force_destroy          = false
      + id                     = (known after apply)
      + key                    = "raw/"
      + kms_key_id             = (known after apply)
      + server_side_encryption = (known after apply)
      + storage_class          = (known after apply)
      + tags_all               = (known after apply)
      + version_id             = (known after apply)
        # (1 unchanged attribute hidden)
    }

Plan: 4 to add, 0 to change, 0 to destroy.

Changes to Outputs:
  + data_lake_bucket = "ph-shoes-data-lake"

Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
