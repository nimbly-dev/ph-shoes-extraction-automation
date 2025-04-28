// ec2/main.tf

resource "tls_private_key" "ec2_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "null_resource" "force_replace_for_iam" {
  triggers = {
    iam_profile = aws_iam_instance_profile.ec2_airflow_profile.id
  }
}

resource "aws_key_pair" "automation_key" {
  key_name   = var.key_name
  public_key = tls_private_key.ec2_key.public_key_openssh
}

resource "aws_security_group" "this" {
  name        = "${var.instance_name}-sg"
  description = "Security group for ${var.instance_name}"

  # SSH
  ingress {
    from_port   = var.ssh_port
    to_port     = var.ssh_port
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }

  # Airflow web UI
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]    # tighten in prod!
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

  tags = merge(var.tags, { Name = var.instance_name })
}

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

resource "aws_instance" "this" {
  ami                    = data.aws_ami.amazon_linux2.id
  instance_type          = var.instance_type
  key_name               = aws_key_pair.automation_key.key_name
  vpc_security_group_ids = [aws_security_group.this.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_airflow_profile.name
  user_data              = templatefile("${path.module}/userdata.tpl", { AWS_REGION = var.aws_region })

  # ensure new instance comes up before destroying old
  lifecycle {
    create_before_destroy = true
    replace_triggered_by  = [aws_iam_instance_profile.ec2_airflow_profile]
    ignore_changes        = [user_data]
  }

  user_data_replace_on_change = true

  depends_on = [
    null_resource.force_replace_for_iam
  ]

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = true
  }

  tags = merge(
    var.tags,
    {
      Name        = var.instance_name
      Environment = var.environment
    }
  )
}

