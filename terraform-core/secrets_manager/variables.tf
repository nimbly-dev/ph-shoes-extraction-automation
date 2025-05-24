variable "secret_name" {
  type        = string
  description = "The name (path) of this secret in SM"
}

variable "description" {
  type        = string
  default     = "Managed by Terraform"
}

variable "tags" {
  type        = map(string)
  default     = {}
}

variable "secret_map" {
  type        = map(string)
  description = "If non-empty, JSON-encode this map into SecretString"
  default     = {}
}

variable "secret_string" {
  type        = string
  description = "If non-empty, store this plaintext directly"
  default     = ""
}

variable "generate_password" {
  type        = bool
  description = "Whether to generate a random password into the map"
  default     = false
}

variable "password_length" {
  type        = number
  description = "Length of generated password"
  default     = 16
}
