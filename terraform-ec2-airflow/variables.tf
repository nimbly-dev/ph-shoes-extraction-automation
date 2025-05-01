variable "aws_region" {
  description = "AWS region to operate in"
  type        = string
}

variable "ec2_key_name" {
  description = "EC2 KeyPair name for SSH access"
  type        = string
}

variable "ec2_instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
}

variable "environment" {
  description = "Deployment environment (e.g. dev, prod)"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "ssh_port" {
  description = "SSH port"
  type        = number
  default     = 22
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "extra_ingress" {
  description = "Additional security-group ingress rules"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}

variable "redeploy_id" {
  description = "Unique value to force EC2 replacement"
  type        = string
}