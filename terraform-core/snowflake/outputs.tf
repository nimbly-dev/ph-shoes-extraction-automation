output "storage_integration_role_arn" {
  description = "ARN of the IAM Role for Snowflake EXTERNAL_STAGE"
  value       = aws_iam_role.snowflake_external_stage.arn
}
