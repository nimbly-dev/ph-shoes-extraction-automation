variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}

variable "ssh_port" {
  description = "SSH port"
  type        = number
  default     = 22
}

variable "ssh_cidr_blocks" {
  description = "Allowed SSH CIDRs"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "extra_ingress" {
  description = "Additional SG ingress rules"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

variable "key_name" {
  description = "EC2 key pair name"
  type        = string
}

variable "artifact_bucket_name" {
  description = "S3 bucket for CodeDeploy artifacts"
  type        = string
}

variable "artifact_bucket_arn" {
  description = "ARN of S3 bucket for artifacts"
  type        = string
}

variable "iam_instance_profile" {
  description = "Name of existing IAM instance-profile to attach; if empty, module creates its own"
  type        = string
  default     = ""
}

variable "vpc_security_group_ids" {
  description = "List of SG IDs to attach; if empty, module creates its own SG"
  type        = list(string)
  default     = []
}
