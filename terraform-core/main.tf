# terraform/main.tf

provider "aws" {
  region = var.aws_region
}

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.93.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

locals {
  common_tags = merge(
    {
      Application = var.app_name
      Environment = var.environment
    },
    var.extra_tags
  )
}

module "s3_data_lake" {
  source      = "./s3_datalake"
  bucket_name = var.s3_datalake_bucket_name
  tags        = local.common_tags
}

module "s3_airflow_codedeploy" {
  source      = "./s3_airflow_codedeploy"
  bucket_name = var.airflow_codedeploy_bucket_name
  environment = var.environment
  tags        = local.common_tags
}

module "automation_lambda_extract" {
  source           = "./lambda"
  lambda_name      = "ph-shoes-extract-lambda"
  lambda_image_uri = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler   = ["handlers.extract.lambda_handler"]
  s3_bucket        = module.s3_data_lake.bucket_name
  tags             = local.common_tags
  aws_region       = var.aws_region
}

module "automation_lambda_clean" {
  source           = "./lambda"
  lambda_name      = "ph-shoes-clean-lambda"
  lambda_image_uri = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler   = ["handlers.clean.lambda_handler"]
  s3_bucket        = module.s3_data_lake.bucket_name
  tags             = local.common_tags
  aws_region       = var.aws_region
}

module "automation_lambda_quality" {
  source           = "./lambda"
  lambda_name      = "ph-shoes-quality-lambda"
  lambda_image_uri = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler   = ["handlers.quality.lambda_handler"]
  s3_bucket        = module.s3_data_lake.bucket_name
  tags             = local.common_tags
  aws_region       = var.aws_region
}

module "automation_lambda_fact_product_shoes_etl" {
  source           = "./lambda"
  lambda_name      = "ph-shoes-product-etl-lambda"
  lambda_image_uri = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler   = ["handlers.product_shoes_etl.lambda_handler"]
  s3_bucket        = module.s3_data_lake.bucket_name
  tags             = local.common_tags
  aws_region       = var.aws_region
}

module "ec2_placeholder" {
  source               = "./ec2_airflow_placeholder"
  aws_region           = var.aws_region
  instance_type        = var.ec2_instance_type
  key_name             = var.ec2_key_name
  instance_name        = var.ec2_instance_name
  environment          = var.environment
  tags                 = local.common_tags
  ssh_port             = var.ssh_port
  ssh_cidr_blocks      = var.ssh_cidr_blocks
  extra_ingress        = var.ec2_extra_ingress
  artifact_bucket_name = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_name
  artifact_bucket_arn  = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_arn
  airflow_api_secret_arn = module.airflow_api_creds.secret_arn
}

module "airflow_api_creds" {
  source       = "./secrets_manager"
  secret_name  = "prod/ph-shoes/airflow-api-creds"
  description  = "Airflow REST API user creds for CI"
  tags         = local.common_tags

  generate_password = true
  secret_map = {
    username = "airflow_service_user"
  }
}

module "codedeploy" {
  source                = "./codedeploy"
  aws_region            = var.aws_region
  app_name              = "ph-shoes-airflow-codedeploy-app"
  deployment_group_name = "ph-shoes-airflow-deployment-group"
  ec2_instance_name     = var.ec2_instance_name
  tags                  = local.common_tags
}

data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "lambda_secrets_policy" {
  name        = "ph-shoes-lambda-secrets-policy"
  description = "Allow Lambda to access Secrets Manager"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action   = ["secretsmanager:GetSecretValue"],
        Effect   = "Allow",
        Resource = "arn:aws:secretsmanager:${var.aws_region}:${data.aws_caller_identity.current.account_id}:secret:prod/ph-shoes/s3-credentials*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_attach_extract" {
  role       = module.automation_lambda_extract.lambda_role_name
  policy_arn = aws_iam_policy.lambda_secrets_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_attach_clean" {
  role       = module.automation_lambda_clean.lambda_role_name
  policy_arn = aws_iam_policy.lambda_secrets_policy.arn
}

resource "aws_iam_role_policy_attachment" "lambda_secrets_attach_quality" {
  role       = module.automation_lambda_quality.lambda_role_name
  policy_arn = aws_iam_policy.lambda_secrets_policy.arn
}

resource "aws_iam_policy" "airflow_lambda_invoke_policy" {
  name        = "ph-shoes-lambda-invoke-policy"
  description = "Allow Airflow to invoke ph-shoes Lambda functions"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow",
        Action   = "lambda:InvokeFunction",
        Resource = "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:ph-shoes-*"
      }
    ]
  })
}

resource "aws_iam_user" "airflow_lambda_invoker" {
  name          = "ph-shoes-airflow-lambda-invoker"
  force_destroy = true
  tags          = local.common_tags
}

resource "aws_iam_user_policy_attachment" "airflow_lambda_invoker_attach" {
  user       = aws_iam_user.airflow_lambda_invoker.name
  policy_arn = aws_iam_policy.airflow_lambda_invoke_policy.arn
}

resource "aws_iam_access_key" "airflow_lambda_invoker" {
  user = aws_iam_user.airflow_lambda_invoker.name
}

module "snowflake_iam" {
  source                   = "./snowflake"
  snowflake_aws_account_id = var.snowflake_aws_account_id
  data_lake_bucket         = var.s3_datalake_bucket_name
}
