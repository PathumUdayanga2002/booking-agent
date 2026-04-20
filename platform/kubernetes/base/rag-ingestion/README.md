# RAG Ingestion Base

This directory defines Kubernetes manifests for S3-backed RAG ingestion.

Target flow:

1. Document uploaded to S3 bucket.
2. Ingestion worker reads object metadata and content.
3. Worker chunks and embeds text.
4. Worker writes vectors to Qdrant.
5. Worker updates ingestion status in the backend.

Planned resources:

- Deployment: `rag-ingestion-worker`
- ConfigMap: non-secret settings (bucket, queue/topic, chunk params)
- Secret reference: AWS credentials via IAM role for service account pattern
- HorizontalPodAutoscaler: optional for backlog handling
