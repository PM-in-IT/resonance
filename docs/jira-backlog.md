# Resonance — Jira backlog

Story points are relative. Suggested DoD for every ticket: merged code, tests pass, no secrets committed, and changed contracts documented.

# Sprint 1 — Upload → processing → indexed transcript

## RES-1 Bootstrap backend project — Backend — 2 SP
Set up FastAPI, settings, test/lint tooling and health endpoint.

**AC**
- `/api/v1/health` returns 200.
- `.env.example` exists.
- application starts locally.
- pytest and Ruff are configured.

## RES-2 Docker development environment — Backend — 3 SP
Dockerfile + Compose for API, worker, PostgreSQL/pgvector and Redis.

**AC**
- one command starts dependencies;
- API connects to DB/Redis;
- API and worker share media volume;
- ffmpeg/ffprobe exist in runtime.

## RES-3 Database schema + Alembic — Backend — 5 SP
Create `audio_assets`, `transcript_segments`, `query_records`; enable pgvector.

**AC**
- migration from empty DB succeeds;
- FK cascade works;
- status/audio-id lookup indexes exist.

## RES-4 Backend ↔ AI contracts — Backend + AI — 3 SP
Freeze `Transcriber`, `Chunker`, `DocumentEmbedder`, `QueryEmbedder`, and `GroundedSummarizer` contracts.

**AC**
- timestamps are milliseconds;
- no Whisper/LangChain/model-specific types leak outside AI package;
- fake/stub implementations can be injected.

## RES-5 Media upload endpoint — Backend — 5 SP
Implement `POST /api/v1/audio`.

**AC**
- multipart upload;
- hard byte limit;
- generated storage key, never raw filename as path;
- returns 202 + audio id/status;
- invalid media returns 422.

## RES-6 10-minute duration validation — Backend — 3 SP
Validate actual media using ffprobe.

**AC**
- duration stored as ms;
- >600 seconds rejected;
- unreadable files rejected;
- temp files cleaned.

## RES-7 Storage abstraction — Backend — 3 SP
Implement `Storage` protocol and local-volume adapter.

**AC**
- API saves by storage key;
- worker resolves same media;
- interface can later support S3 without service changes.

## RES-8 RQ processing + state machine — Backend — 5 SP
Enqueue processing and implement `queued -> processing -> ready/failed`.

**AC**
- request never runs Whisper synchronously;
- job payload is audio id;
- DB is source of truth;
- worker error sets failed;
- timeout configured.

## RES-9 Audio status endpoint — Backend — 2 SP
Implement `GET /api/v1/audio/{id}`.

**AC**
- metadata/status returned;
- 404 for unknown id;
- safe failure message exposed on failed job.

## RES-10 Whisper transcription — AI/ML Person A — 8 SP
Timestamped transcription implementation.

**AC**
- sample under 10 min transcribes successfully;
- timestamps are monotonic and inside media duration;
- non-empty speech produces non-empty transcript;
- conforms to shared DTOs.

## RES-11 Chunking + document embeddings — AI/ML Person B — 8 SP
Convert timestamped transcript to embedding-ready chunks.

**AC**
- every chunk has ordinal/start/end/text/embedding;
- chunk overlap policy documented;
- model/dimension documented;
- document/query embedding space is identical.

## RES-12 Persist indexing result — Backend + AI — 5 SP
Wire the transcription, chunking, and embedding pipeline into the worker and store chunks.

**AC**
- complete result committed atomically;
- retry does not leave duplicate/partial chunks;
- ready only after successful commit;
- error -> rollback + failed.

## RES-13 Sprint-1 integration test — Team — 5 SP
Upload -> queue -> process -> ready.

**AC**
- complete vertical slice verified;
- CI can use deterministic fake/cached AI;
- failure path covered.

# Sprint 2 — Query → timestamp/summary → hardening

## RES-14 Vector similarity repository — Backend — 5 SP
Cosine search in pgvector scoped to one audio id.

**AC**
- takes query embedding + top_k;
- cannot leak chunks from another audio;
- ordered by relevance;
- integration test uses known vectors.

## RES-15 Query embedding — AI/ML Person B — 3 SP
Implement query embedding using the same model as indexed chunks.

**AC**
- dimensions match;
- normalization strategy documented;
- deterministic test mode/fixture available.

## RES-16 Grounded summarizer — AI/ML — 8 SP
Generate concise answer/summary from retrieved chunks only.

**AC**
- prompt/context prevents unsupported extrapolation as far as practical;
- insufficient-context behavior defined;
- result is concise enough for UI.

## RES-17 Query endpoint — Backend — 5 SP
Implement `POST /api/v1/audio/{id}/queries`.

**AC**
- 404 unknown audio;
- 409 unless ready;
- validates question/top_k;
- embeds -> retrieves -> summarizes;
- returns primary timestamp + supporting matches.

## RES-18 Query history — Backend — 2 SP
Persist successful question/result metadata.

**AC**
- successful calls create record;
- failed calls do not;
- correct audio FK.

## RES-19 Stable error model — Backend — 3 SP
Introduce machine-readable domain error codes.

**AC**
At least:
- `MEDIA_TOO_LONG`
- `MEDIA_UNSUPPORTED`
- `AUDIO_NOT_READY`
- `PROCESSING_FAILED`

Internal stack traces/provider secrets are never returned.

## RES-20 Retry/idempotency policy — Backend — 5 SP
Make processing retries safe.

**AC**
- transient failure retryable;
- no duplicate segments;
- no concurrent duplicate processing per audio;
- final failure visible to client.

## RES-21 Backend test suite — Backend — 5 SP
Unit/API tests with fake AI.

**AC**
- covers 202/404/409/422;
- media validation/state transitions covered;
- deterministic query tests require no real model.

## RES-22 AI evaluation dataset — AI/ML — 5 SP
Label recordings/questions with expected relevant timestamp ranges.

**AC**
- multiple recordings and paraphrased questions;
- expected range per query;
- retrieval hit@k (or equivalent) reported;
- failure cases documented.

## RES-23 Retrieval/timestamp tuning — AI/ML + Backend — 5 SP
Tune chunk size, overlap, top_k and primary timestamp policy.

**AC**
- chosen parameters documented;
- primary timestamp rule deterministic;
- measured against baseline.

## RES-24 End-to-end test/demo — Team — 5 SP
Upload -> ready -> question -> timestamp + summary.

**AC**
- test recording <=10 min;
- timestamp is semantically relevant;
- summary is grounded in returned context;
- AI worker failure propagates to status.

## RES-25 Structured logging/correlation — Backend — 3 SP
Log upload/job/query lifecycle with identifiers.

**AC**
- audio_id/job_id present where relevant;
- processing start/end/failure logged;
- no raw media/secrets logged.

## RES-26 CI pipeline — Backend — 3 SP
Run lint/tests on pull requests.

**AC**
- Ruff + pytest;
- test Postgres has pgvector;
- failures block merge per repo policy.

## RES-27 Setup/demo documentation — Team — 3 SP
Document startup, migrations, worker and demo flow.

**AC**
- new teammate can start the stack from README;
- model/API-key requirements documented without committing secrets;
- demo commands cover upload, status polling and query.

# Post-MVP
- S3/MinIO adapter
- auth/user ownership
- delete + retention
- direct video upload/audio extraction
- SSE/WebSocket progress
- HNSW after measurement
- reranker
- rate limiting
