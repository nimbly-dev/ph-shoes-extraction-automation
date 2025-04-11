output "data_lake_bucket" {
  description = "The S3 bucket name for the data lake"
  value       = module.s3_data_lake.bucket_name
}

output "airflow_lambda_invoker_access_key_id" {
  value     = aws_iam_access_key.airflow_lambda_invoker.id
  sensitive = true
}

output "airflow_lambda_invoker_secret_access_key" {
  value     = aws_iam_access_key.airflow_lambda_invoker.secret
  sensitive = true
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = module.ec2_instance.instance_public_ip
}

output "ec2_public_dns" {
  description = "Public DNS of the EC2 instance"
  value       = module.ec2_instance.instance_public_dns
}
