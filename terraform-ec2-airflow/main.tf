
data "terraform_remote_state" "core" {
  backend = "s3"
  config = {
    bucket = "ph-shoes-terraform-state"
    key    = "core/terraform.tfstate"
    region = var.aws_region
  }
}

module "ec2_instance" {
  source           = "../terraform-core/ec2_airflow_placeholder"
  aws_region       = var.aws_region

  # these two must match module's variables.tf:
  key_name         = var.ec2_key_name
  instance_name    = var.ec2_instance_name

  instance_type        = var.instance_type
  environment          = var.environment
  tags                 = var.tags
  ssh_port             = var.ssh_port
  ssh_cidr_blocks      = var.ssh_cidr_blocks
  extra_ingress        = var.extra_ingress

  artifact_bucket_name = data.terraform_remote_state.core.outputs.airflow_codedeploy_bucket_name
  artifact_bucket_arn  = data.terraform_remote_state.core.outputs.airflow_codedeploy_bucket_arn

  iam_instance_profile    = data.terraform_remote_state.core.outputs.ec2_instance_profile_name
  vpc_security_group_ids  = var.vpc_security_group_ids
}

output "ec2_public_ip" {
  value       = module.ec2_instance.instance_public_ip
  description = "Public IP of the Airflow EC2 host"
}

output "ec2_public_dns" {
  value       = module.ec2_instance.instance_public_dns
  description = "Public DNS of the Airflow EC2 host"
}
