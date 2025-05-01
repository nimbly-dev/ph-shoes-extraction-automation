output "iam_instance_profile" {
  value = aws_iam_instance_profile.profile[0].name
}

output "iam_instance_profile_arn" {
  value = aws_iam_instance_profile.profile[0].arn
}

output "instance_public_ip" {
  description = "Public IP of the EC2 instance (empty if none launched)"
  # if aws_instance.this has 1 element, return its public_ip, else empty
  value = length(aws_instance.this) > 0 ? aws_instance.this[0].public_ip : ""
}

output "instance_public_dns" {
  description = "Public DNS of the EC2 instance (empty if none launched)"
  value = length(aws_instance.this) > 0 ? aws_instance.this[0].public_dns : ""
}
