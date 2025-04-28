# ec2/iam.tf

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}

resource "aws_iam_role" "ec2_airflow_role" {
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
  name = "${var.instance_name}-policy"
  role = aws_iam_role.ec2_airflow_role.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "codedeploy:PollHostCommand",
          "codedeploy:UpdateHostCommand"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = ["s3:ListBucket"]
        Resource = [var.artifact_bucket_arn]
      },
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = ["${var.artifact_bucket_arn}/*"]
      },
      {
        Effect = "Allow"
        Action = ["lambda:InvokeFunction"]
        Resource = [
          "arn:aws:lambda:${var.aws_region}:${data.aws_caller_identity.current.account_id}:function:ph-shoes-extract-lambda"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy_agent_access" {
  role       = aws_iam_role.ec2_airflow_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforAWSCodeDeploy"
}

resource "aws_iam_instance_profile" "ec2_airflow_profile" {
  name = "${var.instance_name}-profile"
  role = aws_iam_role.ec2_airflow_role.name
}
