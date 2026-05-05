output "github_actions_role_arn" {
  description = "IAM role ARN for GitHub Actions"
  value       = aws_iam_role.github_actions.arn
}

output "ecr_repo_urls" {
  description = "ECR repository URLs"
  value       = { for key, repo in aws_ecr_repository.repos : key => repo.repository_url }
}

output "ecr_repo_names" {
  description = "ECR repository names"
  value       = { for key, repo in aws_ecr_repository.repos : key => repo.name }
}
