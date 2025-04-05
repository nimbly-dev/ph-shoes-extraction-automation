variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "app_name" {
  description = "Name of the application for tagging"
  type        = string
  default     = "ph-shoes-scrapper-project"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for the data lake"
  type        = string
  default     = "ph-shoes-data-lake"
}
