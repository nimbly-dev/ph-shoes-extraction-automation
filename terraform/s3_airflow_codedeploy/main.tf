resource "aws_s3_bucket" "airflow_codedeploy" {
  bucket = var.bucket_name

  tags = var.tags
}

# Create a marker object to designate the folder for artifacts.
resource "aws_s3_object" "artifact_marker" {
  bucket  = aws_s3_bucket.airflow_codedeploy.id
  key     = "artifacts/"
  content = ""  # Creates a zero-byte object to represent the folder.
}

# Configure lifecycle rules for the artifact bucket.
resource "aws_s3_bucket_lifecycle_configuration" "artifact_expiry" {
  bucket = aws_s3_bucket.airflow_codedeploy.id

  rule {
    id     = "expire-artifacts-after-30-days"
    status = "Enabled"

    filter {
      prefix = "artifacts/"
    }

    expiration {
      days = var.expiration_days
    }
  }
}
