resource "aws_s3_bucket" "data_lake" {
  bucket = var.bucket_name

  tags = var.tags
}

# Removed versioning for raw data
# resource "aws_s3_bucket_versioning" "data_lake" {
#   bucket = aws_s3_bucket.data_lake.id
#
#   versioning_configuration {
#     status = "Enabled"
#   }
# }

resource "aws_s3_object" "raw_prefix_marker" {
  bucket  = aws_s3_bucket.data_lake.id
  key     = "raw/"
  content = ""  # creates a zero-byte object to mark the folder
}

resource "aws_s3_bucket_lifecycle_configuration" "raw_expiry" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "expire-raw-after-30-days"
    status = "Enabled"

    filter {
      prefix = "raw/"
    }

    expiration {
      days = 30
    }

    noncurrent_version_expiration {
      noncurrent_days = 7
    }
  }
}
