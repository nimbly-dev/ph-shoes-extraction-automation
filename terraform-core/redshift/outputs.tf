# output "endpoint" {
#   description = "Redshift cluster endpoint"
#   value       = aws_redshift_cluster.this.endpoint
# }

# output "port" {
#   description = "Redshift port"
#   value       = aws_redshift_cluster.this.port
# }

# output "jdbc_url" {
#   description = "JDBC URL"
#   value       = format(
#     "jdbc:redshift://%s:%d/%s",
#     aws_redshift_cluster.this.endpoint,
#     aws_redshift_cluster.this.port,
#     var.db_name
#   )
# }

# output "s3_role_arn" {
#   description = "IAM role ARN that Redshift uses to COPY from S3"
#   value       = aws_iam_role.s3.arn
# }
