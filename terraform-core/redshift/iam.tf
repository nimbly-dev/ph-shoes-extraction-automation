# // IAM role so Redshift can read from S3
# resource "aws_iam_role" "s3" {
#   name = "${var.cluster_identifier}-s3-role"

#   assume_role_policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect    = "Allow"
#       Principal = { Service = "redshift.amazonaws.com" }
#       Action    = "sts:AssumeRole"
#     }
#     ]
#   })

#   tags = var.tags
# }

# resource "aws_iam_role_policy_attachment" "s3_access" {
#   role       = aws_iam_role.s3.name
#   policy_arn = "arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess"
# }