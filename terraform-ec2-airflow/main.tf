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

  # these four must be passed in via CLI / GitHub Action
  aws_region        = var.aws_region
  key_name          = var.ec2_key_name
  instance_name     = var.ec2_instance_name
  environment       = var.environment

  # these all have defaults in this module’s variables.tf
  instance_type     = var.instance_type
  ssh_port          = var.ssh_port
  ssh_cidr_blocks   = var.ssh_cidr_blocks
  extra_ingress     = var.extra_ingress

  # pulled from core’s remote state — no need to CLI
  artifact_bucket_name = data.terraform_remote_state.core.outputs.airflow_codedeploy_bucket_name
  artifact_bucket_arn  = data.terraform_remote_state.core.outputs.airflow_codedeploy_bucket_arn
}

output "ec2_public_ip" {
  description = "Public IP of the Airflow EC2 host"
  value       = module.ec2_instance.instance_public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the Airflow EC2 host"
  value       = module.ec2_instance.instance_public_dns
}
