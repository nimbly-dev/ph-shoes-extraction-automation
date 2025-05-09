// look up the default VPC
data "aws_vpc" "default" {
  default = true
}

// look up all subnets in that VPC
data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

// security group to allow Redshift ingress
resource "aws_security_group" "this" {
  name        = "${var.cluster_identifier}-sg"
  description = "Allow Redshift TCP ingress"
  vpc_id      = data.aws_vpc.default.id

  revoke_rules_on_delete = true

  ingress {
    from_port   = 5439
    to_port     = 5439
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidrs
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = var.tags
}

// subnet group spanning all default subnets
resource "aws_redshift_subnet_group" "this" {
  name       = "${var.cluster_identifier}-subnet-group"
  subnet_ids = data.aws_subnets.default.ids
  tags       = var.tags
}
