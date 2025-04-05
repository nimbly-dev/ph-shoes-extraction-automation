provider "aws" {
  region = var.aws_region
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
