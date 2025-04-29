output "ssh_private_key_secret_arn" {
  description = "ARN of the secret containing the private SSH key"
  value       = aws_secretsmanager_secret.ssh_private_key.arn
  sensitive   = true
}
