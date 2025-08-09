resource "aws_iam_role" "snowflake_external_stage" {
  name = "snowflake-external-stage-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            # Snowflake’s IAM user principal (from DESCRIBE INTEGRATION)
            "arn:aws:iam::149831570743:user/fu751000-s",
          ]
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            # This must exactly match the integration’s external ID
            "sts:ExternalId" = "UWPPRGY.AQ07622"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "snowflake_external_stage_policy" {
  name = "snowflake-external-stage-policy"
  role = aws_iam_role.snowflake_external_stage.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.data_lake_bucket}"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = [
          "arn:aws:s3:::${var.data_lake_bucket}/*"
        ]
      }
    ]
  })
}
