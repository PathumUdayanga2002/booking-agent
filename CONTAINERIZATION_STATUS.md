# Containerization Status

## Why apps were not containerized before

The repository had Kubernetes manifests, but there were no Dockerfiles for the application services and no compose stack to build runnable images. Kubernetes image references were placeholders only (`ghcr.io/replace-me/...`).

## What is now added

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `agent/Dockerfile`
- `agent_langgraph/Dockerfile`
- Service `.dockerignore` files
- Root `docker-compose.yml` to run local full stack

## Local run

```bash
docker compose up --build
```

Services:
- Frontend: http://localhost:3000
- Backend: http://localhost:5000
- Agent v1: http://localhost:8000
- Agent LangGraph: http://localhost:8001
- Qdrant: http://localhost:6333
- MongoDB: mongodb://localhost:27017

## Important

- Set `GROQ_API_KEY` in your shell before running compose.
- Replace default JWT/admin secrets in `docker-compose.yml` for anything beyond local dev.
