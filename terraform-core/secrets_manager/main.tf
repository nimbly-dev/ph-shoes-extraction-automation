resource "random_password" "this" {
  count            = var.generate_password ? 1 : 0
  length           = var.password_length
  special          = true
  override_special = "!@#%^&*()[]{}"
}

resource "aws_secretsmanager_secret" "this" {
  name        = var.secret_name
  description = var.description
  tags        = var.tags
}

locals {
  final_map = (var.generate_password
    ? merge(var.secret_map, { password = random_password.this[0].result })
    : var.secret_map)
}

resource "aws_secretsmanager_secret_version" "this" {
  secret_id     = aws_secretsmanager_secret.this.id
  secret_string = (length(var.secret_map) > 0 ? jsonencode(var.secret_map) : var.secret_string)
}
