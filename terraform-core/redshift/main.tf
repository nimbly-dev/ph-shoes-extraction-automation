resource "aws_redshift_cluster" "this" {
  cluster_identifier        = var.cluster_identifier
  database_name             = var.db_name
  master_username           = var.master_username
  master_password = var.master_password_plain
  cluster_type              = "single-node"
  node_type                 = var.node_type
  publicly_accessible       = var.publicly_accessible
  vpc_security_group_ids    = [aws_security_group.this.id]
  cluster_subnet_group_name = aws_redshift_subnet_group.this.name
  iam_roles                 = [aws_iam_role.s3.arn]
  skip_final_snapshot       = var.skip_final_snapshot

  timeouts { delete = "60m" }
  tags     = var.tags
}
