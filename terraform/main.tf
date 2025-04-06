provider "aws" {
  region  = var.aws_region
  profile = "terraform"  
}

locals {
  common_tags = {
    Application = var.app_name
    Environment = var.environment
  }
}

module "s3_data_lake" {
  source      = "./s3"
  bucket_name = var.bucket_name
  tags        = local.common_tags
}


module "automation_lambda_extract" {
  source            = "./lambda"
  lambda_name       = "ph-shoes-extract-lambda"
  lambda_image_uri  = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler    = ["handlers.extract.lambda_handler"]
  s3_bucket         = module.s3_data_lake.bucket_name
  tags              = local.common_tags
  aws_region        = var.aws_region
}

module "automation_lambda_clean" {
  source            = "./lambda"
  lambda_name       = "ph-shoes-clean-lambda"
  lambda_image_uri  = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler    = ["handlers.clean.lambda_handler"]
  s3_bucket         = module.s3_data_lake.bucket_name
  tags              = local.common_tags

  aws_region        = var.aws_region
}

module "automation_lambda_quality" {
  source            = "./lambda"
  lambda_name       = "ph-shoes-quality-lambda"
  lambda_image_uri  = "101679083819.dkr.ecr.ap-southeast-1.amazonaws.com/ph-shoes-lambda-shared-repo:latest"
  lambda_handler    = ["handlers.quality.lambda_handler"]
  s3_bucket         = module.s3_data_lake.bucket_name
  tags              = local.common_tags
  aws_region        = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_iam_policy" "lambda_secrets_policy" {
  name        = "ph-shoes-lambda-secrets-policy"
  description = "Allow Lambda to access Secrets Manager"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "secretsmanager:GetSecretValue"
        ],
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
