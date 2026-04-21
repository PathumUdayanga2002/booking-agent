variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "booking-platform"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "vpc_cidr" {
  description = "Dev VPC CIDR"
  type        = string
  default     = "10.20.0.0/16"
}

variable "az_count" {
  description = "AZ count for subnets"
  type        = number
  default     = 2
}

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnet egress"
  type        = bool
  default     = false
}

variable "enable_vpc_endpoints" {
  description = "Enable VPC endpoints for private AWS service access"
  type        = bool
  default     = false
}

variable "enable_s3_gateway_endpoint" {
  description = "Enable S3 gateway endpoint"
  type        = bool
  default     = true
}

variable "interface_endpoint_services" {
  description = "Interface endpoint services to create"
  type        = list(string)
  default = [
    "ecr.api",
    "ecr.dkr",
    "ssm",
    "ec2messages",
    "ssmmessages",
    "logs"
  ]
}

variable "rag_bucket_name" {
  description = "Optional override for RAG S3 bucket name"
  type        = string
  default     = null
}

variable "ami_id" {
  description = "Optional AMI ID override for cluster nodes"
  type        = string
  default     = null
}

variable "key_name" {
  description = "Optional EC2 key pair name"
  type        = string
  default     = null
}

variable "control_plane_instance_type" {
  description = "EC2 instance type for control-plane nodes"
  type        = string
  default     = "t3.small"
}

variable "worker_instance_type" {
  description = "EC2 instance type for worker nodes"
  type        = string
  default     = "t3.small"
}

variable "control_plane_desired" {
  description = "Desired control-plane node count"
  type        = number
  default     = 1
}

variable "control_plane_min" {
  description = "Min control-plane node count"
  type        = number
  default     = 1
}

variable "control_plane_max" {
  description = "Max control-plane node count"
  type        = number
  default     = 1
}

variable "worker_desired" {
  description = "Desired worker node count"
  type        = number
  default     = 2
}

variable "worker_min" {
  description = "Min worker node count"
  type        = number
  default     = 1
}

variable "worker_max" {
  description = "Max worker node count"
  type        = number
  default     = 3
}

variable "kube_api_ingress_cidrs" {
  description = "CIDR blocks allowed to access Kubernetes API"
  type        = list(string)
  default     = []
}

variable "nodeport_ingress_cidrs" {
  description = "CIDR blocks allowed to access worker NodePort range"
  type        = list(string)
  default     = []
}

variable "cluster_name" {
  description = "Kubernetes cluster name used during bootstrap"
  type        = string
  default     = "booking-dev"
}

variable "pod_cidr" {
  description = "Pod CIDR used by kubeadm init"
  type        = string
  default     = "10.244.0.0/16"
}

variable "control_plane_endpoint" {
  description = "DNS/IP endpoint workers use to join control-plane"
  type        = string
  default     = "control-plane.internal"
}

variable "tags" {
  description = "Additional tags"
  type        = map(string)
  default     = {}
}
