# variable "cluster_identifier" {
#   description = "Redshift cluster identifier"
#   type        = string
# }

# variable "db_name" {
#   description = "Database name inside Redshift"
#   type        = string
# }

# variable "master_username" {
#   description = "Master username for Redshift"
#   type        = string
# }

# variable "master_password_plain" {
#   description = "Plain‑text password to seed into Secrets Manager"
#   type        = string
#   sensitive   = true
# }

# variable "node_type" {
#   description = "Redshift node type (e.g. dc2.large to use free‑trial hours)"
#   type        = string
#   default     = "dc2.large"
# }

# variable "publicly_accessible" {
#   description = "Whether the cluster is publicly accessible"
#   type        = bool
#   default     = true
# }

# variable "allowed_cidrs" {
#   description = "CIDR blocks allowed to connect to Redshift port"
#   type        = list(string)
#   default     = ["0.0.0.0/0"]
# }

# variable "skip_final_snapshot" {
#   description = "Skip final snapshot when destroying cluster"
#   type        = bool
#   default     = true
# }

# variable "tags" {
#   description = "Common tags"
#   type        = map(string)
#   default     = {}
# }

# variable "aws_region" {
#   description = "AWS region (e.g. ap-southeast-1)"
#   type        = string
# }
