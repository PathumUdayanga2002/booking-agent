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

  control_plane_user_data = templatefile("${path.module}/userdata/control-plane.sh.tftpl", {
    cluster_name = var.cluster_name
    aws_region   = var.aws_region
    pod_cidr     = var.pod_cidr
  })

  worker_user_data = templatefile("${path.module}/userdata/worker.sh.tftpl", {
    cluster_name           = var.cluster_name
    aws_region             = var.aws_region
    control_plane_endpoint = var.control_plane_endpoint
  })
}

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

module "rag_storage" {
  source = "../../modules/storage"

  bucket_name      = local.computed_rag_bucket_name
  force_destroy    = false
  enable_lifecycle = true
  expiration_days  = 180
  tags             = local.merged_tags
}

module "security" {
  source = "../../modules/security"

  name           = local.name_prefix
  rag_bucket_arn = module.rag_storage.bucket_arn
  tags           = local.merged_tags
}

module "compute" {
  source = "../../modules/compute"

  name               = local.name_prefix
  vpc_id             = module.network.vpc_id
  private_subnet_ids = module.network.private_subnet_ids
  vpc_cidr           = var.vpc_cidr

  ami_id   = var.ami_id
  key_name = var.key_name

  control_plane_instance_profile_name = module.security.control_plane_instance_profile_name
  worker_instance_profile_name        = module.security.worker_instance_profile_name

  control_plane_instance_type = var.control_plane_instance_type
  worker_instance_type        = var.worker_instance_type

  control_plane_desired = var.control_plane_desired
  control_plane_min     = var.control_plane_min
  control_plane_max     = var.control_plane_max

  worker_desired = var.worker_desired
  worker_min     = var.worker_min
  worker_max     = var.worker_max

  kube_api_ingress_cidrs        = var.kube_api_ingress_cidrs
  nodeport_ingress_cidrs        = var.nodeport_ingress_cidrs
  ingress_nlb_security_group_id = var.ingress_nlb_security_group_id

  control_plane_user_data = local.control_plane_user_data
  worker_user_data        = local.worker_user_data

  tags = local.merged_tags
}
