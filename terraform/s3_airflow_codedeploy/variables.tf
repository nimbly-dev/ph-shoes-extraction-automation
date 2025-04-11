variable "bucket_name" {
  description = "Name for the S3 bucket to store Airflow CodeDeploy artifacts"
  type        = string
}

variable "environment" {
  description = "Deployment environment, e.g., dev, prod"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to the bucket"
  type        = map(string)
  default     = {}
}

variable "expiration_days" {
  description = "Number of days after which artifacts expire"
  type        = number
  default     = 7
}
