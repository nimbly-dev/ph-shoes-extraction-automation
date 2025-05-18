# // look up the default VPC
# data "aws_vpc" "default" {
#   default = true
# }

# // look up the VPC’s main route table
# data "aws_route_tables" "main" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.default.id]
#   }
#   filter {
#     name   = "association.main"
#     values = ["true"]
#   }
# }

# // look up all subnets in that VPC
# data "aws_subnets" "default" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.default.id]
#   }
# }

# // lookup current region so we can build the S3 service name
# data "aws_region" "current" {}

# resource "aws_security_group" "this" {
#   name        = "${var.cluster_identifier}-sg"
#   description = "Allow Redshift TCP ingress"
#   vpc_id      = data.aws_vpc.default.id

#   revoke_rules_on_delete = true

#   # only create ingress rules if the module var says you’re public
#   dynamic "ingress" {
#     for_each = var.publicly_accessible ? var.allowed_cidrs : []
#     content {
#       from_port   = 5439
#       to_port     = 5439
#       protocol    = "tcp"
#       cidr_blocks = [ingress.value]
#     }
#   }

#   egress {
#     from_port   = 0
#     to_port     = 0
#     protocol    = "-1"
#     cidr_blocks = ["0.0.0.0/0"]
#   }

#   tags = var.tags
# }

# // subnet group spanning all default subnets
# resource "aws_redshift_subnet_group" "this" {
#   name       = "${var.cluster_identifier}-subnet-group"
#   subnet_ids = data.aws_subnets.default.ids
#   tags       = var.tags
# }

# // —— free S3 gateway endpoint ——
# // routes all S3 traffic over the AWS network (no NAT gateway needed)
# resource "aws_vpc_endpoint" "s3" {
#   vpc_id            = data.aws_vpc.default.id
#   service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
#   vpc_endpoint_type = "Gateway"
#   route_table_ids   = data.aws_route_tables.main.ids
#   tags              = var.tags
# }

# resource "aws_security_group_rule" "allow_dbt_cloud_1" {
#   type              = "ingress"
#   from_port         = 5439
#   to_port           = 5439
#   protocol          = "tcp"
#   cidr_blocks       = ["52.3.77.232/32"]
#   security_group_id = aws_security_group.this.id
# }

# resource "aws_security_group_rule" "allow_dbt_cloud_2" {
#   type              = "ingress"
#   from_port         = 5439
#   to_port           = 5439
#   protocol          = "tcp"
#   cidr_blocks       = ["3.214.191.130/32"]
#   security_group_id = aws_security_group.this.id
# }

# resource "aws_security_group_rule" "allow_dbt_cloud_3" {
#   type              = "ingress"
#   from_port         = 5439
#   to_port           = 5439
#   protocol          = "tcp"
#   cidr_blocks       = ["34.233.79.135/32"]
#   security_group_id = aws_security_group.this.id
# }
