output "data_lake_bucket" {
  description = "The S3 bucket name for the data lake"
  value       = module.s3_data_lake.bucket_name
}
