terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }

  backend "s3" {
    # Initialize with: terraform init -backend-config="key=envs/eks-dev/terraform.tfstate"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.merged_tags
  }
}

data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  default_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    Architecture = "eks"
  }

  merged_tags = merge(local.default_tags, var.tags)
}

# ============================================
# Networking
# ============================================
module "network" {
  source = "../../modules/network"

  name                        = local.name_prefix
  vpc_cidr                    = var.vpc_cidr
  az_count                    = var.az_count
  enable_nat_gateway          = var.enable_nat_gateway
  enable_vpc_endpoints        = var.enable_vpc_endpoints
  enable_s3_gateway_endpoint  = var.enable_s3_gateway_endpoint
  interface_endpoint_services = var.interface_endpoint_services
  tags                        = local.merged_tags
}

# ============================================
# Storage (RAG Documents Bucket)
# ============================================
module "rag_storage" {
  source = "../../modules/storage"

  bucket_name      = local.computed_rag_bucket_name
  force_destroy    = false
  enable_lifecycle = true
  expiration_days  = 180
  tags             = local.merged_tags
}

locals {
  computed_rag_bucket_name = var.rag_bucket_name != null ? var.rag_bucket_name : "${local.name_prefix}-rag-${data.aws_caller_identity.current.account_id}"
}

# ============================================
# EKS Cluster
# ============================================
module "eks" {
  source = "../../modules/eks"

  cluster_name           = "${local.name_prefix}-eks"
  kubernetes_version     = var.kubernetes_version
  vpc_id                 = module.network.vpc_id
  subnet_ids             = module.network.private_subnet_ids
  enabled_cluster_log_types = var.enabled_cluster_log_types
  log_retention_days     = var.log_retention_days

  enable_addons = {
    vpc_cni    = true
    ebs_csi    = true
    coredns    = true
    kube_proxy = true
  }

  tags = local.merged_tags
}

# ============================================
# Worker Node IAM Role - S3 RAG Bucket Access
# ============================================
resource "aws_iam_policy" "node_rag_bucket_access" {
  name        = "${local.name_prefix}-node-rag-access"
  description = "Policy for EKS nodes to access RAG S3 bucket"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.rag_storage.bucket_arn,
          "${module.rag_storage.bucket_arn}/*"
        ]
      }
    ]
  })

  tags = local.merged_tags
}

resource "aws_iam_role_policy_attachment" "node_rag_access" {
  policy_arn = aws_iam_policy.node_rag_bucket_access.arn
  role       = module.eks.node_role_arn
}

# ============================================
# Outputs
# ============================================
output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_ca_certificate" {
  description = "EKS cluster CA certificate (base64)"
  value       = module.eks.cluster_ca_certificate
  sensitive   = true
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.network.private_subnet_ids
}

output "rag_bucket_name" {
  description = "RAG documents S3 bucket name"
  value       = module.rag_storage.bucket_name
}

output "rag_bucket_arn" {
  description = "RAG documents S3 bucket ARN"
  value       = module.rag_storage.bucket_arn
}

output "kubeconfig_command" {
  description = "Command to configure kubectl for this cluster"
  value       = "aws eks update-kubeconfig --name ${module.eks.cluster_name} --region ${var.aws_region}"
}
