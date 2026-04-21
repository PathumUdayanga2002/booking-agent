data "aws_iam_policy_document" "ec2_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "control_plane" {
  name               = "${var.name}-control-plane-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = var.tags
}

resource "aws_iam_role" "worker" {
  name               = "${var.name}-worker-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy_attachment" "control_plane_ssm" {
  role       = aws_iam_role.control_plane.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "control_plane_ecr" {
  role       = aws_iam_role.control_plane.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "control_plane_cw" {
  role       = aws_iam_role.control_plane.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_role_policy_attachment" "worker_ssm" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "worker_ecr" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_role_policy_attachment" "worker_cw" {
  role       = aws_iam_role.worker.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_policy" "worker_rag_s3" {
  name        = "${var.name}-worker-rag-s3-policy"
  description = "Least-privilege S3 access for RAG ingestion workloads running on worker nodes"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListRagBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket",
          "s3:GetBucketLocation"
        ]
        Resource = [var.rag_bucket_arn]
      },
      {
        Sid    = "ReadWriteRagObjects"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload"
        ]
        Resource = ["${var.rag_bucket_arn}/*"]
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "worker_rag_s3" {
  role       = aws_iam_role.worker.name
  policy_arn = aws_iam_policy.worker_rag_s3.arn
}

resource "aws_iam_instance_profile" "control_plane" {
  name = "${var.name}-control-plane-profile"
  role = aws_iam_role.control_plane.name
  tags = var.tags
}

resource "aws_iam_instance_profile" "worker" {
  name = "${var.name}-worker-profile"
  role = aws_iam_role.worker.name
  tags = var.tags
}
