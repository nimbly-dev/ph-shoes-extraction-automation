resource "aws_iam_role" "snowflake_external_stage" {
  name = "snowflake-external-stage-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::101679083819:root",
            "arn:aws:iam::287263346869:user/xem01000-s"
          ]
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "sts:ExternalId" = "NEZCEFP-VH40477"
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
