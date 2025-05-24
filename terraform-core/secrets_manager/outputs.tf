output "secret_arn" {
  value       = aws_secretsmanager_secret.this.arn
  description = "ARN of the created secret"
}

output "secret_id" {
  value       = aws_secretsmanager_secret.this.id
  description = "ID of the created secret"
}
