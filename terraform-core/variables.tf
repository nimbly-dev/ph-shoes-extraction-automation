variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "app_name" {
  description = "Name of the application for tagging"
  type        = string
  default     = "ph-shoes-scrapper-project"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "s3_datalake_bucket_name" {
  description = "Name of the S3 bucket for the data lake"
  type        = string
  default     = "ph-shoes-data-lake"
}

variable "airflow_codedeploy_bucket_name" {
  description = "The S3 bucket name for Airflow CodeDeploy artifacts"
  type        = string
  default     = "ph-shoes-airflow-artifacts"
}

variable "extra_tags" {
  description = "Additional tags to apply to resources"
  type        = map(string)
  default     = {}
}

# EC2-placeholder inputs
variable "ec2_instance_type" {
  description = "EC2 instance type for the Airflow host"
  type        = string
  default     = "t2.micro"
}

variable "ec2_key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  default     = "ec2-ph-shoes-automation-keypair-name"
}

variable "ec2_instance_name" {
  description = "Name for the EC2 instance"
  type        = string
  default     = "airflow-ec2"
}

variable "ssh_port" {
  description = "SSH port for the EC2 instance"
  type        = number
  default     = 22
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "ec2_extra_ingress" {
  description = "Extra ingress rules for the EC2 security group"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}
