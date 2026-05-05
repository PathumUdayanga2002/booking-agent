variable "cluster_name" {
  description = "Name of the EKS cluster"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.29"
}

variable "vpc_id" {
  description = "VPC ID where cluster will be created"
  type        = string
}

variable "subnet_ids" {
  description = "List of subnet IDs for cluster (private subnets recommended)"
  type        = list(string)
}

variable "cluster_security_group_id" {
  description = "Optional security group ID for cluster. If not provided, one will be created"
  type        = string
  default     = null
}

variable "enable_addons" {
  description = "Map of EKS add-ons to enable"
  type = object({
    vpc_cni = bool
    ebs_csi = bool
    coredns = bool
    kube_proxy = bool
  })
  default = {
    vpc_cni = true
    ebs_csi = true
    coredns = true
    kube_proxy = true
  }
}

variable "enabled_cluster_log_types" {
  description = "List of control plane log types to enable"
  type        = list(string)
  default     = ["api", "audit", "authenticator", "controllerManager", "scheduler"]
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
