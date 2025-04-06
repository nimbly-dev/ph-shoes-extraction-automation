resource "aws_iam_role" "lambda_exec" {
  name = "${var.lambda_name}-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_lambda_function" "lambda" {
  function_name = var.lambda_name
  package_type  = "Image"
  image_uri     = var.lambda_image_uri
  role          = aws_iam_role.lambda_exec.arn

  timeout     = 840
  memory_size = 512

  image_config {
    command = var.lambda_handler
  }

  environment {
    variables = {
      S3_BUCKET = var.s3_bucket
    }
  }

  tags = var.tags
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.lambda_name}-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ],
        Resource = [
          "arn:aws:s3:::${var.s3_bucket}",
          "arn:aws:s3:::${var.s3_bucket}/*"
        ]
      }
    ]
  })
}

output "lambda_role_name" {
  value = aws_iam_role.lambda_exec.name
}
