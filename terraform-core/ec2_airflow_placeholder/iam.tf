
data "aws_caller_identity" "current" {}
data "aws_iam_policy" "airflow_lambda_invoke_policy" {
  arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/ph-shoes-lambda-invoke-policy"
}

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

resource "aws_iam_role_policy" "inline" {
  count  = var.iam_instance_profile == "" ? 1 : 0
  name   = "${var.instance_name}-policy"
  role   = aws_iam_role.ec2_airflow_role[0].name
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      # ECR
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken",
          "ecr:BatchGetImage",
          "ecr:GetDownloadUrlForLayer",
        ]
        Resource = "*"
      },
      # CodeDeploy agent
      {
        Effect   = "Allow"
        Action   = ["codedeploy:PollHostCommand", "codedeploy:UpdateHostCommand"]
        Resource = "*"
      },
      # S3 read your artifacts
      {
        Effect   = "Allow"
        Action   = ["s3:ListBucket"]
        Resource = [var.artifact_bucket_arn]
      },
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:GetObjectVersion"]
        Resource = ["${var.artifact_bucket_arn}/*"]
      },
    ]
  })
}

resource "aws_iam_instance_profile" "profile" {
  count = var.iam_instance_profile == "" ? 1 : 0
  name  = "${var.instance_name}-profile"
  role  = aws_iam_role.ec2_airflow_role[0].name
}

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

data "aws_iam_instance_profile" "imported" {
  count = var.iam_instance_profile != "" ? 1 : 0
  name  = var.iam_instance_profile
}

resource "aws_iam_role_policy_attachment" "ssm_core_imported" {
  count      = var.iam_instance_profile != "" ? 1 : 0
  role       = data.aws_iam_instance_profile.imported[0].role_name   
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}
