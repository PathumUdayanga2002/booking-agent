variable "name" {
  description = "Name prefix for compute resources"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ASGs"
  type        = list(string)
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "ami_id" {
  description = "Optional AMI ID override"
  type        = string
  default     = null
}

variable "key_name" {
  description = "Optional EC2 key pair name"
  type        = string
  default     = null
}

variable "control_plane_instance_profile_name" {
  description = "IAM instance profile name for control-plane nodes"
  type        = string
}

variable "worker_instance_profile_name" {
  description = "IAM instance profile name for worker nodes"
  type        = string
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

variable "enable_detailed_monitoring" {
  description = "Enable EC2 detailed monitoring"
  type        = bool
  default     = true
}

variable "kube_api_ingress_cidrs" {
  description = "CIDR blocks allowed to access Kubernetes API server"
  type        = list(string)
  default     = []
}

variable "nodeport_ingress_cidrs" {
  description = "CIDR blocks allowed for NodePort traffic to workers"
  type        = list(string)
  default     = []
}

variable "control_plane_user_data" {
  description = "User data script for control-plane nodes"
  type        = string
  default     = "#!/bin/bash\necho control-plane-bootstrap > /var/log/k8s-bootstrap.log\n"
}

variable "worker_user_data" {
  description = "User data script for worker nodes"
  type        = string
  default     = "#!/bin/bash\necho worker-bootstrap > /var/log/k8s-bootstrap.log\n"
}

variable "tags" {
  description = "Common tags"
  type        = map(string)
  default     = {}
}
