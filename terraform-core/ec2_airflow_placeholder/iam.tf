data "aws_caller_identity" "current" {}

resource "aws_iam_role" "ec2_airflow_role" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
  tags = var.tags
}

resource "aws_iam_role_policy" "inline" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-policy"
  role  = aws_iam_role.ec2_airflow_role[0].id
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
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "codedeploy_access" {
  count      = var.iam_instance_profile == "" ? 1 : 0
  role       = aws_iam_role.ec2_airflow_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2RoleforAWSCodeDeploy"
}

resource "aws_iam_instance_profile" "profile" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-profile"
  role  = aws_iam_role.ec2_airflow_role[0].name
}
