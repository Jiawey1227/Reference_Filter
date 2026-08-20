## Why

The current Tkinter GUI is difficult to evolve into a modern, guided workflow, and the editable provider/model fields allow users to enter unsupported combinations. Moving to a local web app with locked Qwen/DashScope models gives users a cleaner interface while keeping the scoring workflow predictable.

## What Changes

- **BREAKING**: Replace the Tkinter GUI workflow with a local frontend/backend web application.
- Lock AI provider/model configuration to Qwen/DashScope:
  - Base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
  - Embedding model: `text-embedding-v4`
  - LLM model: `qwen3.6-flash`
- Remove user-editable Base URL, embedding model, and LLM model controls from the UI.
- Keep a single user-provided API key for both embedding and LLM calls.
- Add a Python web backend that exposes job creation, status, cancellation, connection testing, and result download endpoints.
- Add a modern frontend that supports file upload, run mode selection, threshold configuration, topic entry, progress display, logs, cancellation, and result download.
- Enforce Qwen embedding request batch limits internally instead of requiring the user to know provider limits.
- Isolate embedding cache entries by model/provider so old embeddings cannot pollute Qwen scores.
- Update documentation for the new local web workflow and fixed Qwen configuration.

## Capabilities

### New Capabilities
- `qwen-web-app`: Local web application workflow for running Qwen-locked academic literature scoring jobs.

### Modified Capabilities
- None.

## Impact

- Affects the GUI entry point, runtime configuration, embedding cache behavior, API validation, and user documentation.
- Adds backend dependencies such as `fastapi`, `uvicorn`, and `python-multipart`.
- Adds a separate frontend project, recommended as React + Vite + TypeScript.
- Existing `main.py` scoring logic should be reused where practical, but must support fixed Qwen configuration and job progress/cancel callbacks from the web backend.
