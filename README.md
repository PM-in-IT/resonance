# Resonance

Resonance accepts a short lecture/media recording, processes it asynchronously, and lets a user ask a natural-language question. The API returns an approximate matching timestamp plus a concise summary grounded in relevant transcript fragments.

## Architecture

**Modular monolith**, one repository and one application model:

- FastAPI — HTTP API
- PostgreSQL + pgvector — metadata, transcript chunks, embeddings, query history
- Redis + RQ — background processing queue
- local storage in development, replaceable by an S3-compatible adapter
- `app/ai/` — stable AI contracts and model-specific implementations

The API process and worker process import the same application package; they are not separate microservices.

## Start locally

```bash
cp .env.example .env
docker compose up --build
docker compose exec api alembic upgrade head
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- Ollama: `http://localhost:11434`
