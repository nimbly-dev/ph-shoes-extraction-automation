terraform {
  backend "s3" {
    bucket  = "ph-shoes-terraform-state"
    key     = "ec2-airflow/terraform.tfstate"
    region  = var.aws_region
    encrypt = true
  }
}
