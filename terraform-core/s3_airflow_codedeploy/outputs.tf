output "airflow_codedeploy_bucket_name" {
  description = "The name of the S3 bucket for Airflow CodeDeploy artifacts"
  value       = aws_s3_bucket.airflow_codedeploy.bucket
}

output "airflow_codedeploy_bucket_arn" {
  description = "The ARN of the S3 bucket for Airflow CodeDeploy artifacts"
  value       = aws_s3_bucket.airflow_codedeploy.arn
}
