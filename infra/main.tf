# ContextPilot AI — AWS deployment stub (ECS Fargate + RDS + ElastiCache + S3)
#
# This is a starting skeleton, not a turnkey deploy: fill in VPC/subnet ids,
# container image URIs, and secrets before running `terraform apply`.
# All sensitive values are pulled from variables — never hardcode real
# credentials here.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

resource "aws_ecr_repository" "backend" {
  name                 = "${var.project_name}-backend"
  image_tag_mutability = "IMMUTABLE"
}

resource "aws_ecr_repository" "frontend" {
  name                 = "${var.project_name}-frontend"
  image_tag_mutability = "IMMUTABLE"
}

resource "aws_db_instance" "postgres" {
  identifier             = "${var.project_name}-db"
  engine                 = "postgres"
  engine_version         = "16"
  instance_class         = var.db_instance_class
  allocated_storage      = 20
  db_name                = "contextpilot"
  username               = var.db_username
  password               = var.db_password
  skip_final_snapshot    = true
  publicly_accessible    = false
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "${var.project_name}-redis"
  engine                = "redis"
  node_type             = var.redis_node_type
  num_cache_nodes       = 1
  parameter_group_name  = "default.redis7"
}

resource "aws_s3_bucket" "documents" {
  bucket = "${var.project_name}-documents-${var.environment}"
}

resource "aws_secretsmanager_secret" "llm_api_keys" {
  name = "${var.project_name}/${var.environment}/llm-api-keys"
}

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-${var.environment}"
}

# NOTE: aws_ecs_task_definition / aws_ecs_service / ALB / security groups /
# VPC wiring are intentionally left out of this stub — see deployment-guide.md
# for the manual steps until this is filled in for your AWS account layout.
