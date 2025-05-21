# terraform-core/ec2_airflow_placeholder/iam.tf

# who am I
data "aws_caller_identity" "current" {}

# bring in the already-created “ph-shoes-lambda-invoke-policy” so this module can attach it
data "aws_iam_policy" "airflow_lambda_invoke_policy" {
  arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/ph-shoes-lambda-invoke-policy"
}

# EC2 role for running Airflow
resource "aws_iam_role" "ec2_airflow_role" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

# inline permissions for ECR, CodeDeploy, S3
resource "aws_iam_role_policy" "inline" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-policy"
  role  = aws_iam_role.ec2_airflow_role[0].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer"
        ]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = [
          "codedeploy:PollHostCommand",
          "codedeploy:UpdateHostCommand"
        ]
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
      }
    ]
  })
}

# instance profile so EC2 can assume the above role
resource "aws_iam_instance_profile" "profile" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-profile"
  role  = aws_iam_role.ec2_airflow_role[0].name
}

# attach CodeDeploy-managed policy so Airflow can call Lambda
resource "aws_iam_role_policy_attachment" "allow_lambda_invoke_ec2" {
  count      = var.iam_instance_profile == "" ? 1 : 0
  role       = aws_iam_role.ec2_airflow_role[0].name
  policy_arn = data.aws_iam_policy.airflow_lambda_invoke_policy.arn
}

resource "aws_iam_role_policy_attachment" "ssm_core" {
  count      = var.iam_instance_profile == "" ? 1 : 0
  role       = aws_iam_role.ec2_airflow_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ssm_core_imported" {
  count      = var.iam_instance_profile != "" ? 1 : 0
  role       = var.iam_instance_profile
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}