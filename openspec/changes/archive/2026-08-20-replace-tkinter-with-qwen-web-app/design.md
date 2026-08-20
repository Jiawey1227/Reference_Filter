## Context

The current application is a Tkinter desktop tool backed by `main.py`. The core scoring flow already supports progress callbacks, cancellation checks, embedding-only mode, LLM-only mode, full mode, Excel output, and country highlighting. The new web workflow should reuse that domain logic where practical while replacing the user-facing GUI and locking provider/model choices.

## Goals / Non-Goals

**Goals:**
- Provide a local web application with a Python backend and separate frontend.
- Keep the scoring workflow local to the user's machine.
- Lock provider/model settings in code rather than exposing them as user-editable fields.
- Preserve current run modes and Excel output semantics.
- Make long-running jobs observable through progress, logs, cancellation, and result download.
- Add provider-aware cache behavior so Qwen embeddings are not mixed with older model vectors.

**Non-Goals:**
- Multi-user authentication or hosted deployment.
- Cloud storage for uploaded Excel files or generated results.
- Supporting arbitrary AI providers or user-editable model names.
- Rewriting the scoring algorithm from scratch.
- Maintaining the Tkinter GUI as the primary interface after migration.

## Decisions

### Use FastAPI for the backend

FastAPI fits the local API shape, file uploads, JSON status endpoints, and background job orchestration without adding a large framework. It also keeps the project in Python so the backend can call the existing scoring logic directly.

Alternative considered: Flask. Flask would work, but FastAPI gives clearer request/response models and built-in OpenAPI docs, which helps keep the API contract explicit.

### Use React + Vite + TypeScript for the frontend

The frontend should be a modern single-page app with responsive layout, file upload, job polling, logs, and stateful controls. React + Vite keeps the setup lightweight while giving a strong component model for job state and form state.

Alternative considered: server-rendered HTML. That would reduce the JavaScript toolchain, but it would make progress polling, file upload state, and modern UI interactions less ergonomic.

### Keep one API key and fixed Qwen constants

The backend should define fixed constants for:

```text
QWEN_BASE_URL = https://dashscope-intl.aliyuncs.com/compatible-mode/v1
EMBEDDING_MODEL = text-embedding-v4
LLM_MODEL = qwen3.6-flash
EMBEDDING_MAX_BATCH_SIZE = 10
```

The user provides a single DashScope-compatible API key. The key is used by both embedding and LLM clients. The frontend shows provider/model values as read-only information.

Alternative considered: separate embedding and LLM keys. That adds flexibility, but the user explicitly wants one key and locked models.

### Introduce a job manager around existing scoring callbacks

The backend should expose:

```text
POST /api/config/test
POST /api/jobs
GET  /api/jobs/{job_id}
POST /api/jobs/{job_id}/cancel
GET  /api/jobs/{job_id}/download
```

Jobs can run in background threads because the existing scoring function is blocking and I/O-bound. Each job stores status, progress, logs, result path, error message, cancellation flag, and timestamps. The scoring callback appends log messages and progress updates into job state. The cancellation endpoint flips a flag that the existing cancellation callback reads.

Alternative considered: task queue. A full queue is unnecessary for a local single-user app and would complicate setup.

### Refactor scoring configuration without changing the algorithm

`main.py` should gain a provider/model configuration path that can be called by the web backend. The existing cosine similarity, threshold routing, LLM JSON parsing, Excel output, and country highlighting behavior should remain recognizable.

The embedding request path must split provider requests into chunks of at most 10 texts while still honoring the user's larger batch preference as an outer processing preference.

### Make embedding cache provider-aware

The existing cache is keyed by normalized text only, which is unsafe after changing embedding models. The cache should include provider/model identity in the key or move to a model-specific cache file. Either approach is acceptable if Qwen `text-embedding-v4` vectors cannot be confused with older vectors.

Recommended approach: model-specific cache file path such as `cache/embedding_cache_qwen_text-embedding-v4.pkl`, plus defensive keying that includes model identity for future safety.

### Serve frontend and backend during development separately

Development should run the backend with Uvicorn and the frontend with Vite. For packaged/local production use, the backend may optionally serve the built frontend static assets, but that can be added after the core migration works.

## Risks / Trade-offs

- Qwen embedding API limits may differ by region or account -> enforce a hard max of 10 texts per embedding call and surface API errors clearly.
- Frontend toolchain adds Node.js dependency -> document setup and keep the frontend project minimal.
- Long-running local jobs may leave temporary files behind after crashes -> store uploads/results in a dedicated runtime directory and document cleanup expectations.
- Existing Chinese UI text appears to have encoding issues in source files -> new frontend should use UTF-8 files and avoid copying garbled strings.
- LLM JSON response formatting may vary by Qwen model -> keep conservative JSON parsing and fallback behavior from the current implementation.

## Migration Plan

1. Add backend files and dependency declarations.
2. Refactor or wrap scoring code to accept fixed Qwen configuration and provider-aware cache behavior.
3. Add job endpoints and verify upload, progress, cancellation, and download behavior.
4. Add the React/Vite frontend and connect it to the backend API.
5. Update documentation for setup and running the local web app.
6. Keep `gui.py` temporarily during migration if useful, but make the web app the documented primary entry point.

Rollback is straightforward while `main.py` behavior remains compatible: restore the previous GUI entry point and ignore the new backend/frontend directories.
