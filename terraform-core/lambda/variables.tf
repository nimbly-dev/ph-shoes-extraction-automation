variable "lambda_name" {
  description = "Lambda function name"
  type        = string
}

variable "lambda_image_uri" {
  description = "URI of Docker image in ECR"
  type        = string
}

variable "lambda_handler" {
  description = "Handler entry point in Docker image"
  type        = list(string)
}

variable "s3_bucket" {
  description = "S3 bucket name for data lake"
  type        = string
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
}

variable "aws_region" {
  type        = string
}
