variable "aws_region" {
  type        = string
  description = "AWS region where CodeDeploy is created"
  default     = "ap-southeast-1"
}

variable "app_name" {
  type        = string
  description = "Name for the CodeDeploy Application"
}

variable "deployment_group_name" {
  type        = string
  description = "Name for the CodeDeploy Deployment Group"
  default     = "ph-shoes-airflow-deployment-group"
}

variable "ec2_instance_name" {
  type        = string
  description = "Name tag of the EC2 instance targeted by CodeDeploy"
}

variable "tags" {
  type        = map(string)
  description = "Common tags to apply to CodeDeploy resources"
  default     = {}
}
