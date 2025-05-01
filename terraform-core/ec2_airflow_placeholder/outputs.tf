output "iam_instance_profile" {
  description = "Name of the IAM instance-profile for EC2-Airflow"
  value       = var.iam_instance_profile != "" ? var.iam_instance_profile : aws_iam_instance_profile.profile[0].name
}

output "iam_instance_profile_arn" {
  description = "ARN of the IAM instance-profile for EC2-Airflow"
  value       = var.iam_instance_profile != "" ? var.iam_instance_profile : aws_iam_instance_profile.profile[0].arn
}

output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.this[0].id
}

output "instance_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.this[0].public_ip
}

output "instance_public_dns" {
  description = "The public DNS of the EC2 instance"
  value       = aws_instance.this[0].public_dns
}

output "ec2_private_key_pem" {
  description = "The private key (in PEM format) generated for SSH access"
  value       = tls_private_key.ec2_key[0].private_key_pem
  sensitive   = true
}
