terraform {
  backend "s3" {
    bucket  = "ph-shoes-terraform-state"
    key     = "core/terraform.tfstate"
    region  = "ap-southeast-1"
    encrypt = true
  }
}
