variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "booking-app"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "eks-dev"
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS"
  type        = string
  default     = "1.29"
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for private AWS services"
  type        = bool
  default     = false
}

variable "enable_s3_gateway_endpoint" {
  description = "Enable S3 gateway endpoint"
  type        = bool
  default     = true
}

variable "interface_endpoint_services" {
  description = "List of interface endpoints (e.g., ec2, elasticloadbalancing)"
  type        = list(string)
  default     = ["ec2", "elasticloadbalancing"]
}

variable "rag_bucket_name" {
  description = "Custom name for RAG bucket (optional)"
  type        = string
  default     = null
}

variable "enabled_cluster_log_types" {
  description = "List of EKS cluster log types to enable"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "log_retention_days" {
  description = "CloudWatch log retention days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Additional tags to apply"
  type        = map(string)
  default     = {}
}
