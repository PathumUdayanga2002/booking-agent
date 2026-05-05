data "aws_caller_identity" "current" {}

# EKS Cluster IAM Role
resource "aws_iam_role" "cluster_role" {
  name = "${var.cluster_name}-cluster-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "eks.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "cluster_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster_role.name
}

resource "aws_iam_role_policy_attachment" "vpc_resource_controller" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSVPCResourceController"
  role       = aws_iam_role.cluster_role.name
}

# Cluster Security Group
resource "aws_security_group" "cluster" {
  count = var.cluster_security_group_id == null ? 1 : 0

  name        = "${var.cluster_name}-cluster-sg"
  description = "Security group for ${var.cluster_name} EKS cluster"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-cluster-sg"
  })
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "cluster" {
  name              = "/aws/eks/${var.cluster_name}/cluster"
  retention_in_days = var.log_retention_days

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-logs"
  })
}

# EKS Cluster
resource "aws_eks_cluster" "main" {
  name            = var.cluster_name
  role_arn        = aws_iam_role.cluster_role.arn
  version         = var.kubernetes_version
  vpc_config {
    subnet_ids              = var.subnet_ids
    security_groups         = var.cluster_security_group_id != null ? [var.cluster_security_group_id] : [aws_security_group.cluster[0].id]
    endpoint_private_access = true
    endpoint_public_access  = true
  }

  enabled_cluster_log_types = var.enabled_cluster_log_types

  depends_on = [
    aws_iam_role_policy_attachment.cluster_policy,
    aws_iam_role_policy_attachment.vpc_resource_controller,
    aws_cloudwatch_log_group.cluster,
  ]

  tags = merge(var.tags, {
    Name = var.cluster_name
  })
}

# OIDC Provider for IRSA (IAM Roles for Service Accounts)
data "tls_certificate" "cluster" {
  url = aws_eks_cluster.main.identity[0].oidc[0].issuer
}

resource "aws_iam_openid_connect_provider" "cluster" {
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.cluster.certificates[0].sha1_fingerprint]
  url             = aws_eks_cluster.main.identity[0].oidc[0].issuer

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-irsa"
  })
}

# VPC CNI Add-on
resource "aws_eks_addon" "vpc_cni" {
  count = var.enable_addons.vpc_cni ? 1 : 0

  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "vpc-cni"
  addon_version            = data.aws_eks_addon_version.vpc_cni[0].version
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_node_group.main]
}

data "aws_eks_addon_version" "vpc_cni" {
  count           = var.enable_addons.vpc_cni ? 1 : 0
  addon_name      = "vpc-cni"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent     = true
}

# CoreDNS Add-on
resource "aws_eks_addon" "coredns" {
  count = var.enable_addons.coredns ? 1 : 0

  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "coredns"
  addon_version            = data.aws_eks_addon_version.coredns[0].version
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_node_group.main]
}

data "aws_eks_addon_version" "coredns" {
  count           = var.enable_addons.coredns ? 1 : 0
  addon_name      = "coredns"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent     = true
}

# kube-proxy Add-on
resource "aws_eks_addon" "kube_proxy" {
  count = var.enable_addons.kube_proxy ? 1 : 0

  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "kube-proxy"
  addon_version            = data.aws_eks_addon_version.kube_proxy[0].version
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_node_group.main]
}

data "aws_eks_addon_version" "kube_proxy" {
  count           = var.enable_addons.kube_proxy ? 1 : 0
  addon_name      = "kube-proxy"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent     = true
}

# EBS CSI Driver Add-on (for persistent volumes)
resource "aws_iam_role" "ebs_csi_role" {
  count = var.enable_addons.ebs_csi ? 1 : 0
  name  = "${var.cluster_name}-ebs-csi-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRoleWithWebIdentity"
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.cluster.arn
      }
      Condition = {
        StringEquals = {
          "${replace(aws_iam_openid_connect_provider.cluster.url, "https://", "")}:sub" = "system:serviceaccount:kube-system:ebs-csi-controller-sa"
        }
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ebs_csi_policy" {
  count      = var.enable_addons.ebs_csi ? 1 : 0
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
  role       = aws_iam_role.ebs_csi_role[0].name
}

resource "aws_eks_addon" "ebs_csi" {
  count = var.enable_addons.ebs_csi ? 1 : 0

  cluster_name             = aws_eks_cluster.main.name
  addon_name               = "aws-ebs-csi-driver"
  addon_version            = data.aws_eks_addon_version.ebs_csi[0].version
  service_account_role_arn = aws_iam_role.ebs_csi_role[0].arn
  resolve_conflicts_on_update = "OVERWRITE"

  depends_on = [aws_eks_node_group.main]
}

data "aws_eks_addon_version" "ebs_csi" {
  count           = var.enable_addons.ebs_csi ? 1 : 0
  addon_name      = "aws-ebs-csi-driver"
  kubernetes_version = aws_eks_cluster.main.version
  most_recent     = true
}

# Node Group IAM Role
resource "aws_iam_role" "node_role" {
  name = "${var.cluster_name}-node-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "node_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_role.name
}

resource "aws_iam_role_policy_attachment" "cni_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_role.name
}

resource "aws_iam_role_policy_attachment" "registry_policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_role.name
}

# Node Security Group
resource "aws_security_group" "node" {
  name        = "${var.cluster_name}-node-sg"
  description = "Security group for ${var.cluster_name} EKS nodes"
  vpc_id      = var.vpc_id

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "tcp"
    security_groups = [aws_security_group.cluster[0].id]
  }

  ingress {
    from_port       = 0
    to_port         = 65535
    protocol        = "udp"
    security_groups = [aws_security_group.cluster[0].id]
  }

  ingress {
    from_port   = 0
    to_port     = 65535
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-node-sg"
  })
}

# Default Node Group
resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "${var.cluster_name}-default-ng"
  node_role_arn   = aws_iam_role.node_role.arn
  subnet_ids      = var.subnet_ids
  version         = var.kubernetes_version

  scaling_config {
    desired_size = 2
    min_size     = 1
    max_size     = 4
  }

  instance_types = ["t3.medium"]

  vpc_config {
    security_groups = [aws_security_group.node.id]
  }

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-default-ng"
  })

  depends_on = [
    aws_iam_role_policy_attachment.node_policy,
    aws_iam_role_policy_attachment.cni_policy,
    aws_iam_role_policy_attachment.registry_policy,
  ]
}
