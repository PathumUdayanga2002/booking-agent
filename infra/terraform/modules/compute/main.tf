data "aws_ami" "amazon_linux_2" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  selected_ami = var.ami_id != null ? var.ami_id : data.aws_ami.amazon_linux_2.id
}

resource "aws_security_group" "control_plane" {
  name        = "${var.name}-control-plane-sg"
  description = "Control-plane security group"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name}-control-plane-sg"
    Role = "k8s-control-plane"
  })
}

resource "aws_security_group" "worker" {
  name        = "${var.name}-worker-sg"
  description = "Worker security group"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name}-worker-sg"
    Role = "k8s-worker"
  })
}

resource "aws_vpc_security_group_egress_rule" "control_plane_all" {
  security_group_id = aws_security_group.control_plane.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_egress_rule" "worker_all" {
  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_self" {
  security_group_id            = aws_security_group.control_plane.id
  referenced_security_group_id = aws_security_group.control_plane.id
  ip_protocol                  = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_from_worker_api" {
  security_group_id            = aws_security_group.control_plane.id
  referenced_security_group_id = aws_security_group.worker.id
  from_port                    = 6443
  to_port                      = 6443
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_from_worker_kubelet" {
  security_group_id            = aws_security_group.control_plane.id
  referenced_security_group_id = aws_security_group.worker.id
  from_port                    = 10250
  to_port                      = 10250
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_etcd" {
  security_group_id            = aws_security_group.control_plane.id
  referenced_security_group_id = aws_security_group.control_plane.id
  from_port                    = 2379
  to_port                      = 2380
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_components" {
  for_each = {
    scheduler = 10259
    manager   = 10257
  }

  security_group_id            = aws_security_group.control_plane.id
  referenced_security_group_id = aws_security_group.control_plane.id
  from_port                    = each.value
  to_port                      = each.value
  ip_protocol                  = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "control_plane_api_admin" {
  for_each = toset(var.kube_api_ingress_cidrs)

  security_group_id = aws_security_group.control_plane.id
  cidr_ipv4         = each.value
  from_port         = 6443
  to_port           = 6443
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "worker_from_control_plane" {
  security_group_id            = aws_security_group.worker.id
  referenced_security_group_id = aws_security_group.control_plane.id
  ip_protocol                  = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "worker_self" {
  security_group_id            = aws_security_group.worker.id
  referenced_security_group_id = aws_security_group.worker.id
  ip_protocol                  = "-1"
}

resource "aws_vpc_security_group_ingress_rule" "worker_nodeport" {
  for_each = toset(var.nodeport_ingress_cidrs)

  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = each.value
  from_port         = 30000
  to_port           = 32767
  ip_protocol       = "tcp"
}

resource "aws_vpc_security_group_ingress_rule" "worker_internal_nodeport" {
  security_group_id = aws_security_group.worker.id
  cidr_ipv4         = var.vpc_cidr
  from_port         = 30000
  to_port           = 32767
  ip_protocol       = "tcp"
}

resource "aws_launch_template" "control_plane" {
  name_prefix   = "${var.name}-cp-"
  image_id      = local.selected_ami
  instance_type = var.control_plane_instance_type
  key_name      = var.key_name

  iam_instance_profile {
    name = var.control_plane_instance_profile_name
  }

  vpc_security_group_ids = [aws_security_group.control_plane.id]

  user_data = base64encode(var.control_plane_user_data)

  monitoring {
    enabled = var.enable_detailed_monitoring
  }

  metadata_options {
    http_tokens = "required"
  }

  tag_specifications {
    resource_type = "instance"

    tags = merge(var.tags, {
      Name = "${var.name}-control-plane"
      Role = "k8s-control-plane"
    })
  }

  tags = var.tags
}

resource "aws_launch_template" "worker" {
  name_prefix   = "${var.name}-worker-"
  image_id      = local.selected_ami
  instance_type = var.worker_instance_type
  key_name      = var.key_name

  iam_instance_profile {
    name = var.worker_instance_profile_name
  }

  vpc_security_group_ids = [aws_security_group.worker.id]

  user_data = base64encode(var.worker_user_data)

  monitoring {
    enabled = var.enable_detailed_monitoring
  }

  metadata_options {
    http_tokens = "required"
  }

  tag_specifications {
    resource_type = "instance"

    tags = merge(var.tags, {
      Name = "${var.name}-worker"
      Role = "k8s-worker"
    })
  }

  tags = var.tags
}

resource "aws_autoscaling_group" "control_plane" {
  name                = "${var.name}-control-plane-asg"
  desired_capacity    = var.control_plane_desired
  min_size            = var.control_plane_min
  max_size            = var.control_plane_max
  vpc_zone_identifier = var.private_subnet_ids
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.control_plane.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.name}-control-plane"
    propagate_at_launch = true
  }

  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}

resource "aws_autoscaling_group" "worker" {
  name                = "${var.name}-worker-asg"
  desired_capacity    = var.worker_desired
  min_size            = var.worker_min
  max_size            = var.worker_max
  vpc_zone_identifier = var.private_subnet_ids
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.worker.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.name}-worker"
    propagate_at_launch = true
  }

  dynamic "tag" {
    for_each = var.tags
    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}
