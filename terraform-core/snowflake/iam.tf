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
            "arn:aws:iam::203834214384:user/nya21000-s",

            # Snowflake’s own AWS account root (if you want the role-based path too)
            "arn:aws:iam::101679083819:role/snowflake-external-stage-role"
          ]
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            # This must exactly match the integration’s external ID
            "sts:ExternalId" = "GXIVRPJ-PB63809"
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
