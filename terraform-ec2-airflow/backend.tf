terraform {
  backend "s3" {
    bucket  = "ph-shoes-terraform-state"
    key     = "ec2-airflow/terraform.tfstate"
    region  = "ap-southeast-1"
    encrypt = true
  }
}
