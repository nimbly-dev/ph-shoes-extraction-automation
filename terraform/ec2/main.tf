# Generate an RSA private key using the TLS provider.
resource "tls_private_key" "ec2_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}

resource "aws_security_group" "this" {
  name        = "${var.instance_name}-sg"
  description = "Security group for ${var.instance_name}"

  # Allow SSH access
  ingress {
    from_port   = var.ssh_port
    to_port     = var.ssh_port
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }
  
  # Optionally open extra ports (e.g. for webserver)
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

  tags = merge(
    var.tags,
    { Name = var.instance_name }
  )
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
  user_data              = file("${path.module}/userdata.sh")
  tags = merge(
    var.tags,
    {
      Name        = var.instance_name,
      Environment = var.environment
    }
  )
}

resource "aws_iam_role_policy" "ec2_airflow_policy" {
  name = "${var.instance_name}-inline-policy"
  role = aws_iam_role.ec2_airflow_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "secretsmanager:GetSecretValue"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "ssm:DescribeInstanceInformation",
          "ssm:StartSession",
          "ssm:SendCommand"
        ],
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_airflow_profile" {
  name = "${var.instance_name}-instance-profile"
  role = aws_iam_role.ec2_airflow_role.name
}


resource "aws_key_pair" "automation_key" {
  key_name   = var.key_name
  public_key = tls_private_key.ec2_key.public_key_openssh
}
