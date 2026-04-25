# Phase 3 Kubernetes Bootstrap and Manifests

## Scope

This runbook covers applying Kubernetes manifests created for Phase 3.

## Structure

- `platform/kubernetes/base` contains shared manifests.
- `platform/kubernetes/overlays/dev` contains dev customization.
- `platform/kubernetes/overlays/staging` contains staging customization.
- `platform/kubernetes/overlays/prod` contains production customization.

## Prerequisites

1. kubeconfig points to your EC2 kubeadm cluster.
2. StorageClass `gp3` exists (or update qdrant StatefulSet storage class).
3. Secret values are replaced before applying.

## Apply (dev)

```bash
kubectl apply -k platform/kubernetes/overlays/dev
```

## Verify

```bash
kubectl get ns
kubectl -n booking-app get deploy,sts,svc,ingress,hpa
kubectl -n booking-app get pods
```

## Notes

1. `secret.example.yaml` is a template and must be replaced by real secrets management.
2. Ingress hosts are placeholders (`*.booking.local`) and should be updated to real DNS names.
3. Image names are placeholders (`ghcr.io/replace-me/...`) and should be replaced by your registry images.
