provider "aws" {
  region = var.aws_region
}

# pull in your CodeDeploy-artifact bucket name & arn from core
data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = "ph-shoes-terraform-state"
    key    = "core/terraform.tfstate"
    region = var.aws_region
  }
}

module "ec2_instance" {
  source        = "../terraform-core/ec2_airflow_placeholder"
  aws_region    = var.aws_region
  instance_type = var.instance_type
  key_name      = var.ec2_key_name
  instance_name = var.ec2_instance_name
  environment   = var.environment
  tags          = var.tags
  ssh_port      = var.ssh_port
  ssh_cidr_blocks = var.ssh_cidr_blocks
  extra_ingress   = var.extra_ingress

  # just for the EC2-role policy
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
