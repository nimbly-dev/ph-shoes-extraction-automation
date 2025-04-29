output "instance_id" {
  description = "The ID of the EC2 instance"
  value       = aws_instance.this.id
}

output "instance_public_ip" {
  description = "The public IP address of the EC2 instance"
  value       = aws_instance.this.public_ip
}

output "instance_public_dns" {
  description = "The public DNS of the EC2 instance"
  value       = aws_instance.this.public_dns
}

output "ec2_private_key_pem" {
  description = "The private key (in PEM format) generated for SSH access by Terraform"
  value       = tls_private_key.ec2_key.private_key_pem
  sensitive   = true
}
