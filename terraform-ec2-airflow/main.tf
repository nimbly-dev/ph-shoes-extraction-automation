provider "aws" {
  region = var.aws_region
}

data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = "ph-shoes-terraform-state"
    key    = "core/terraform.tfstate"
    region = var.aws_region
  }
}

module "ec2_instance" {
  source = "../terraform-core/ec2_airflow_placeholder"

  # these four come from your GitHub Action inputs
  aws_region        = var.aws_region
  key_name          = var.ec2_key_name
  instance_name     = var.ec2_instance_name
  environment       = var.environment
  redeploy_id       = var.redeploy_id

  # tell the placeholder module to skip IAM creation!
  iam_instance_profile = data.terraform_remote_state.core.outputs.iam_instance_profile_name

  # everything below has defaults in this root or is wired via remote state
  instance_type        = var.instance_type
  ssh_port             = var.ssh_port
  ssh_cidr_blocks      = var.ssh_cidr_blocks
  extra_ingress        = var.extra_ingress

  artifact_bucket_name = data.terraform_remote_state.core.outputs.airflow_codedeploy_bucket_name
  artifact_bucket_arn  = data.terraform_remote_state.core.outputs.airflow_codedeploy_bucket_arn
  airflow_api_secret_arn = data.terraform_remote_state.core.outputs.airflow_api_secret_arn
}

output "ec2_public_ip" {
  value = module.ec2_instance.instance_public_ip
}

output "ec2_public_dns" {
  value = module.ec2_instance.instance_public_dns
}
