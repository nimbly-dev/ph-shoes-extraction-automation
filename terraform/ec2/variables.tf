variable "aws_region" {
  description = "Region for the instance"
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
  description = "Deployment environment (e.g., dev, prod)"
  type        = string
}

variable "tags" {
  description = "Common tags to apply"
  type        = map(string)
  default     = {}
}

variable "ssh_port" {
  description = "Port for SSH access"
  type        = number
  default     = 22
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# Optional list of extra ingress rules for the security group.
variable "extra_ingress" {
  description = "Additional ingress rules (list of maps) for the EC2 security group"
  type = list(object({
    from_port   = number
    to_port     = number
    protocol    = string
    cidr_blocks = list(string)
  }))
  default = []
}


variable "key_name" {
  description = "EC2 key pair name for SSH access"
  type        = string
  default     = "ec2-ph-shoes-automation-keypair-name"
}

variable "public_key_path" {
  description = "Absolute path to the public key file for the EC2 key pair"
  type        = string
  default     = null
}