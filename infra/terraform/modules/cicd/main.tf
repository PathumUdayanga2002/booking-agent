locals {
  github_provider_url = "https://token.actions.githubusercontent.com"
  default_subjects = [
    "repo:${var.github_org}/${var.github_repo}:ref:refs/heads/${var.github_branch}"
  ]
  oidc_subjects = length(var.allowed_subjects) > 0 ? var.allowed_subjects : local.default_subjects
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = local.github_provider_url
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["6938fd4d98bab03faadb97b34396831e3780aea1"]

  tags = merge(var.tags, {
    Name = "github-actions-oidc"
  })
}

resource "aws_iam_role" "github_actions" {
  name = "${var.github_org}-${var.github_repo}-ci-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRoleWithWebIdentity"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = local.oidc_subjects
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_ecr_repository" "repos" {
  for_each = var.ecr_repository_names

  name                 = each.value
  image_tag_mutability = "IMMUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = merge(var.tags, {
    Name = each.value
  })
}

resource "aws_ecr_lifecycle_policy" "repo_policy" {
  for_each = aws_ecr_repository.repos

  repository = each.value.name
  policy     = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 50 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 50
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

data "aws_iam_policy_document" "github_actions" {
  statement {
    sid = "EcrAuthorization"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }

  statement {
    sid = "EcrPushPull"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:BatchGetImage",
      "ecr:CompleteLayerUpload",
      "ecr:GetDownloadUrlForLayer",
      "ecr:InitiateLayerUpload",
      "ecr:PutImage",
      "ecr:UploadLayerPart",
      "ecr:DescribeRepositories"
    ]
    resources = [for repo in aws_ecr_repository.repos : repo.arn]
  }

  statement {
    sid = "EksDescribe"
    actions = [
      "eks:DescribeCluster"
    ]
    resources = [var.eks_cluster_arn]
  }

  statement {
    sid = "StsRead"
    actions = [
      "sts:GetCallerIdentity"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_policy" "github_actions" {
  name        = "${var.github_org}-${var.github_repo}-ci-policy"
  description = "CI/CD permissions for GitHub Actions"
  policy      = data.aws_iam_policy_document.github_actions.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "github_actions" {
  role       = aws_iam_role.github_actions.name
  policy_arn = aws_iam_policy.github_actions.arn
}
