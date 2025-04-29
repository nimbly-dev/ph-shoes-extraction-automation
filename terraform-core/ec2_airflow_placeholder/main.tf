provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

# IAM Role & Profile (only when not passed in)
resource "aws_iam_role" "ec2_airflow_role" {
  count = var.iam_instance_profile == "" ? 1 : 0

  name = "${var.instance_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ec2_airflow_inline_policy" {
  count = var.iam_instance_profile == "" ? 1 : 0

  name = "${var.instance_name}-policy"
  role = aws_iam_role.ec2_airflow_role[0].id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken","ecr:BatchGetImage","ecr:GetDownloadUrlForLayer"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["codedeploy:PollHostCommand","codedeploy:UpdateHostCommand"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [var.artifact_bucket_arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject","s3:GetObjectVersion"]
        Resource = ["${var.artifact_bucket_arn}/*"]
      },
      {
        Effect   = "Allow"
        Action   = ["lambda:InvokeFunction"]
        Resource = ["arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:ph-shoes-extract-lambda"]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy_agent_access" {
  count      = var.iam_instance_profile == "" ? 1 : 0
  role       = aws_iam_role.ec2_airflow_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforAWSCodeDeploy"
}

resource "aws_iam_instance_profile" "ec2_airflow_profile" {
  count = var.iam_instance_profile == "" ? 1 : 0

  name = "${var.instance_name}-profile"
  role = aws_iam_role.ec2_airflow_role[0].name
}

# SSH key pair
resource "tls_private_key" "ec2_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "aws_key_pair" "automation_key" {
  key_name   = var.key_name
  public_key = tls_private_key.ec2_key.public_key_openssh
}

# Security Group
resource "aws_security_group" "this" {
  name        = "${var.instance_name}-sg"
  description = "Security group for ${var.instance_name}"

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
}

# Latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux2" {
  most_recent = true

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "owner-alias"
    values = ["amazon"]
  }

  filter {
    name   = "owner-id"
    values = ["137112412989"]
  }
}

# EC2 Instance
resource "aws_instance" "this" {
  ami           = data.aws_ami.amazon_linux2.id
  instance_type = var.instance_type
  key_name      = aws_key_pair.automation_key.key_name

  vpc_security_group_ids = length(var.vpc_security_group_ids) > 0 ? var.vpc_security_group_ids : [aws_security_group.this.id]

  iam_instance_profile = var.iam_instance_profile != "" ? var.iam_instance_profile : aws_iam_instance_profile.ec2_airflow_profile[0].name

  user_data = templatefile("${path.module}/userdata.tpl", { AWS_REGION = var.aws_region })

  lifecycle {
    create_before_destroy = true
    replace_triggered_by  = [aws_iam_instance_profile.ec2_airflow_profile]
    ignore_changes        = [user_data]
  }

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = merge(var.tags, { Name = var.instance_name, Environment = var.environment })
}
