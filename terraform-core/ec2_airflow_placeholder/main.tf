locals {
  launch = var.iam_instance_profile != ""
}

# generate a keypair only if we are launching
resource "tls_private_key" "ec2_key" {
  count     = local.launch ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = 2048
}

# import-safe EC2 KeyPair
resource "aws_key_pair" "automation_key" {
  count      = local.launch ? 1 : 0
  key_name   = var.key_name
  public_key = tls_private_key.ec2_key[0].public_key_openssh

  lifecycle {
    ignore_changes = [ public_key ]
  }
}

# import-safe Security Group
resource "aws_security_group" "this" {
  count       = local.launch ? 1 : 0
  name        = "${var.instance_name}-sg"
  description = "SG for ${var.instance_name}"

  ingress {
    from_port   = var.ssh_port
    to_port     = var.ssh_port
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }

  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  dynamic "ingress" {
    for_each = var.extra_ingress
    content {
      from_port   = ingress.value.from_port
      to_port     = ingress.value.to_port
      protocol    = ingress.value.protocol
      cidr_blocks = ingress.value.cidr_blocks
    }
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = var.instance_name, Environment = var.environment })

  lifecycle {
    ignore_changes = [ description ]
  }
}

data "aws_ami" "amazon_linux2" {
  most_recent = true
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
  owners = ["137112412989"]
}

# actual EC2 instance
resource "aws_instance" "this" {
  count                  = local.launch ? 1 : 0
  ami                    = data.aws_ami.amazon_linux2.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.automation_key[0].key_name
  vpc_security_group_ids = (length(var.vpc_security_group_ids) > 0 ? var.vpc_security_group_ids : [aws_security_group.this[0].id])
  iam_instance_profile   = var.iam_instance_profile
  user_data              = templatefile("${path.module}/userdata.tpl", { AWS_REGION = var.aws_region })

  lifecycle {
    create_before_destroy = true
    ignore_changes        = [ user_data ]
  }

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = merge(var.tags, { Name = var.instance_name, Environment = var.environment, Redeploy   = var.redeploy_id })
}
