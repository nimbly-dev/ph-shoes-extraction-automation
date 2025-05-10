# Grant this Lambda permission to call Redshift Data API
resource "aws_iam_policy" "lambda_redshift_data_api" {
  name        = "${var.lambda_name}-redshift-data-api"
  description = "Allow Lambda to execute Redshift Data API statements"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = [
        "redshift-data:ExecuteStatement",
        "redshift-data:DescribeStatement",
        "redshift-data:GetStatementResult"
      ],
      Resource = "*"
    }]
  })
}

# Attach it to the Lambda's execution role
resource "aws_iam_role_policy_attachment" "attach_redshift_data_api" {
  role       = aws_iam_role.lambda_exec.name    
  policy_arn = aws_iam_policy.lambda_redshift_data_api.arn
}