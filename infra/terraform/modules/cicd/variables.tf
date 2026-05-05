variable "github_org" {
  description = "GitHub organization or user name"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

variable "github_branch" {
  description = "Allowed branch for GitHub Actions OIDC"
  type        = string
  default     = "main"
}

variable "allowed_subjects" {
  description = "Optional list of allowed OIDC subjects for GitHub Actions"
  type        = list(string)
  default     = []
}

variable "eks_cluster_arn" {
  description = "EKS cluster ARN for describe permissions"
  type        = string
}

variable "ecr_repository_names" {
  description = "Map of service names to ECR repository names"
  type        = map(string)
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
