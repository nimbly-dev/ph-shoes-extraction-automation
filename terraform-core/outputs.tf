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

output "airflow_api_secret_arn" {
  description = "ARN of the Secrets Manager secret with the Airflow REST API user/password"
  value       = module.airflow_api_creds.secret_arn
  sensitive   = true
}

output "bucket_name" {
  description = "Alias: CodeDeploy artifact bucket name"
  value       = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_name
}

output "bucket_arn" {
  description = "Alias: CodeDeploy artifact bucket ARN"
  value       = module.s3_airflow_codedeploy.airflow_codedeploy_bucket_arn
}


output "ec2_instance_profile_name" {
  value = module.ec2_placeholder.iam_instance_profile
}

output "iam_instance_profile_name" {
  description = "EC2 Airflow IAM Instance-Profile"
  value       = module.ec2_placeholder.iam_instance_profile
}

output "snowflake_storage_integration_role_arn" {
  description = "The IAM Role ARN for Snowflake external stage"
  value       = module.snowflake_iam.storage_integration_role_arn
}


# output "redshift_endpoint" {
#   value = module.redshift.endpoint
# }

# output "redshift_admin_password" {
#   description = "Admin password for Redshift (randomly generated)"
#   value       = random_password.redshift.result
#   sensitive   = true
# }

# output "redshift_s3_role_arn" {
#   description = "IAM role ARN that Redshift uses to COPY from S3"
#   value       = module.redshift.s3_role_arn
# }