variable "snowflake_aws_account_id" {
  description = "12-digit AWS account that Snowflake uses"
  type        = string
}

variable "snowflake_account_locator" {
  description = "Snowflake Account Identifier (ExternalId from UI)"
  type        = string
  default     = "PVKLVJX-QC16717"
}

variable "data_lake_bucket" {
  description = "Your S3 bucket where raw files live"
  type        = string
}