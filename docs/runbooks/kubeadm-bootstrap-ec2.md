# Kubeadm Bootstrap Runbook (EC2, No EKS)

## Scope

This runbook covers Phase 2 bootstrap for self-managed Kubernetes on EC2 created by Terraform.

## Preconditions

1. Terraform `envs/dev` apply has completed.
2. EC2 instances are healthy in both ASGs.
3. Access path is available through AWS SSM Session Manager.

## 1. Get Terraform Outputs

```powershell
cd infra/terraform/envs/dev
terraform output
```

Key outputs:
- `control_plane_asg_name`
- `worker_asg_name`
- `node_instance_profile_name`
- `control_plane_security_group_id`
- `worker_security_group_id`

## 2. Verify Control-Plane Bootstrap

Connect to control-plane instance via SSM and verify:

```bash
sudo cat /var/log/k8s-bootstrap.log
sudo test -f /etc/kubernetes/admin.conf && echo "control-plane initialized"
```

Expected:
- `admin.conf` exists
- `/opt/kubeadm-join.sh` exists

## 3. Install CNI on Control Plane

Example (Calico):

```bash
kubectl --kubeconfig=/etc/kubernetes/admin.conf apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.2/manifests/calico.yaml
```

## 4. Join Worker Nodes

1. Read join command from control-plane:

```bash
sudo cat /opt/kubeadm-join.sh
```

2. Connect to each worker with SSM and run the join command using sudo.

## 5. Validate Cluster

On control-plane:

```bash
kubectl --kubeconfig=/etc/kubernetes/admin.conf get nodes -o wide
kubectl --kubeconfig=/etc/kubernetes/admin.conf get pods -A
```

Expected:
- control-plane and workers are `Ready`
- CNI pods are healthy

## 6. Post-Bootstrap Hardening

1. Store kubeconfig securely for ops access.
2. Restrict Kubernetes API ingress CIDRs in Terraform vars.
3. Keep NodePort CIDRs minimal and route traffic via ingress controller.

## Notes

- Worker userdata intentionally does not auto-join, so cluster join remains explicit and controlled.
- For HA expansion later, move to 3 control-plane nodes and use a stable control-plane endpoint (NLB/DNS).
