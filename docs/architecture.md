# Resonance architecture

## Scope

MVP:
- upload one media/audio file up to 10 minutes;
- process it asynchronously;
- ask a natural-language question;
- return a concise grounded summary plus an approximate timestamp and supporting chunks.

Not MVP: authentication, live transcription, collaboration, multi-recording search, SSE/WebSocket progress, microservices.

## Architectural style

**Modular monolith.**

Runtime:
1. `api` — FastAPI.
2. `worker` — RQ worker importing the same `app/` package.
3. PostgreSQL + pgvector.
4. Redis as transient queue.
5. Local media volume in development; S3-compatible adapter can be added later.

The worker does not make this a microservice: there is one codebase, one domain model, one database, and no network API between API and worker.

## Ownership boundary

### Backend owns
- HTTP contracts and validation;
- file storage and duration probing;
- DB schema/migrations;
- job orchestration and status lifecycle;
- persistence of transcript chunks/embeddings;
- generic vector similarity search;
- errors, config, Docker, CI, tests and observability.

### AI/ML owns
- Whisper/model choice;
- transcription and timestamp quality;
- chunking;
- embedding model;
- query embeddings;
- retrieval tuning/reranking;
- grounded summary generation;
- evaluation dataset and quality metrics.

## Stable integration contracts

`AudioIndexer.index(path) -> Sequence[IndexedChunk]`

Each chunk:
- `ordinal`
- `start_ms`
- `end_ms`
- `text`
- `embedding`

`QueryEmbedder.embed_query(question) -> list[float]`

`GroundedSummarizer.summarize(question, chunks) -> str`

Model-specific imports should stay inside the AI implementation package, not HTTP/service/repository code.

## Upload flow

```text
Client
 -> POST /api/v1/audio
 -> byte-size validation
 -> temp file
 -> ffprobe actual duration <= 600 s
 -> media storage
 -> INSERT audio_assets(status=queued)
 -> enqueue RQ job
 <- 202 Accepted

Worker
 -> status=processing
 -> AudioIndexer.index(media)
 -> persist timestamped chunks + embeddings
 -> status=ready
```

Failure -> `failed`, with safe message in PostgreSQL.

## Query flow

```text
Client
 -> POST /api/v1/audio/{id}/queries
 -> require status=ready
 -> QueryEmbedder
 -> pgvector cosine search WHERE audio_id=...
 -> top-k chunks
 -> GroundedSummarizer
 -> persist query record
 <- summary + primary timestamp + supporting matches
```

## State machine

`queued -> processing -> ready`

`queued/processing -> failed`

PostgreSQL is the user-facing source of truth; Redis status is operational only.

## Tables

### audio_assets
`id`, filename, content_type, storage_key, size_bytes, duration_ms, status,
processing_job_id, failure_message, created_at, updated_at.

### transcript_segments
`id`, `audio_id`, `ordinal`, `start_ms`, `end_ms`, `text`, `embedding`.

Unique `(audio_id, ordinal)`.

### query_records
`id`, `audio_id`, question, summary, primary_start_ms, primary_end_ms, created_at.

## API

### POST `/api/v1/audio`
Multipart field `file`.
Returns `202`.

### GET `/api/v1/audio/{audio_id}`
Frontend polling endpoint.

### POST `/api/v1/audio/{audio_id}/queries`

```json
{
  "question": "Where does the lecturer explain CAP theorem?",
  "top_k": 5
}
```

Returns:
```json
{
  "question": "...",
  "summary": "...",
  "primary_start_ms": 173000,
  "primary_end_ms": 201000,
  "matches": [
    {"start_ms": 173000, "end_ms": 201000, "text": "..."}
  ]
}
```

## Design choices

- Use `UploadFile`, not `bytes`, so large upload bodies are spooled instead of necessarily loaded fully into memory.
- Probe actual media with `ffprobe`; do not trust extension/MIME alone.
- Heavy transcription/indexing runs in RQ, not FastAPI request/background task execution.
- Use pgvector inside PostgreSQL instead of introducing a separate vector DB for this MVP.
- For a 10-minute recording, exact cosine search is enough initially; add HNSW only after measurements.
- Leave vector dimension unpinned until the AI team freezes the embedding model, then add a migration with the chosen dimension.
