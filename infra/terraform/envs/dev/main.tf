data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  default_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  merged_tags = merge(local.default_tags, var.tags)

  computed_rag_bucket_name = var.rag_bucket_name != null ? var.rag_bucket_name : "${local.name_prefix}-rag-${data.aws_caller_identity.current.account_id}"
}

module "network" {
  source = "../../modules/network"

  name               = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  az_count           = var.az_count
  enable_nat_gateway = var.enable_nat_gateway
  tags               = local.merged_tags
}

module "rag_storage" {
  source = "../../modules/storage"

  bucket_name      = local.computed_rag_bucket_name
  force_destroy    = false
  enable_lifecycle = true
  expiration_days  = 180
  tags             = local.merged_tags
}
