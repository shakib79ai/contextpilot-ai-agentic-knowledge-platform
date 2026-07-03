variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "contextpilot-ai"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "db_instance_class" {
  type    = string
  default = "db.t4g.micro"
}

variable "redis_node_type" {
  type    = string
  default = "cache.t4g.micro"
}

variable "db_username" {
  type      = string
  default   = "contextpilot"
  sensitive = true
}

variable "db_password" {
  type      = string
  # Dummy placeholder — override via prod.tfvars or TF_VAR_db_password, never commit a real value.
  default   = "REPLACE_WITH_A_REAL_DB_PASSWORD"
  sensitive = true
}
