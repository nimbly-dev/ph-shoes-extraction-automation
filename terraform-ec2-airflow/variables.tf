variable "aws_region"           { type = string }
variable "instance_type"        { type = string }
variable "key_name"             { type = string }
variable "instance_name"        { type = string }
variable "environment"          { type = string }
variable "tags" {
  type    = map(string)
  default = {}
}
variable "ssh_port"             { type = number }
variable "ssh_cidr_blocks"      { type = list(string) }
variable "extra_ingress" {
  type = list(object({
    from_port   = number,
    to_port     = number,
    protocol    = string,
    cidr_blocks = list(string)
  }))
  default = []
}
variable "artifact_bucket_name" { type = string }
variable "artifact_bucket_arn"  { type = string }
variable "vpc_security_group_ids" {
  type    = list(string)
  default = []
}

variable "ec2_key_name" {
  description = "EC2 KeyPair name for SSH access"
  type        = string
}

variable "ec2_instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
}

