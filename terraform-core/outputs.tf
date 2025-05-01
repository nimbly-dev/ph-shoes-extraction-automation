output "data_lake_bucket" {
  description = "The S3 bucket name for the data lake"
  value       = module.s3_data_lake.bucket_name
}

output "airflow_lambda_invoker_access_key_id" {
  description = "Access key ID for the Airflow Lambda invoker user"
  value       = aws_iam_access_key.airflow_lambda_invoker.id
  sensitive   = true
}

output "airflow_lambda_invoker_secret_access_key" {
  description = "Secret access key for the Airflow Lambda invoker user"
  value       = aws_iam_access_key.airflow_lambda_invoker.secret
  sensitive   = true
}
# output "ec2_public_ip" {
#   description = "Public IP address of the EC2 instance"
#   value       = module.ec2_placeholder.instance_public_ip
# }
#
# output "ec2_public_dns" {
#   description = "Public DNS of the EC2 instance"
#   value       = module.ec2_placeholder.instance_public_dns
# }

output "airflow_codedeploy_bucket_name" {
  description = "S3 bucket name used for Airflow CodeDeploy artifacts"
  value       = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_name
}

output "airflow_codedeploy_bucket_arn" {
  description = "S3 bucket ARN used for Airflow CodeDeploy artifacts"
  value       = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_arn
}

output "bucket_name" {
  description = "Alias: CodeDeploy artifact bucket name"
  value       = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_name
}

output "bucket_arn" {
  description = "Alias: CodeDeploy artifact bucket ARN"
  value       = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_arn
}
