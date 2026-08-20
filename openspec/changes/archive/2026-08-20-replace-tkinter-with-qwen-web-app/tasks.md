## 1. Scoring Core And Configuration

- [x] 1.1 Add fixed Qwen/DashScope provider constants and verify no runtime path accepts user-supplied Base URL or model names for the web workflow
- [x] 1.2 Refactor scoring client creation so embedding and LLM calls use the fixed Qwen base URL and the single supplied API key, verified with a small mocked or dry-run client test
- [x] 1.3 Enforce `text-embedding-v4` request chunks of at most 10 texts and verify a batch larger than 10 is split into multiple embedding calls
- [x] 1.4 Make embedding cache provider/model aware and verify old text-only cache entries are not reused for Qwen `text-embedding-v4`
- [x] 1.5 Preserve full, embedding-only, and LLM-only scoring behavior and verify each mode can still produce the expected Excel output columns

## 2. Backend Web API

- [x] 2.1 Add backend dependencies and module structure, then verify the backend imports successfully
- [x] 2.2 Implement `POST /api/config/test` using the fixed Qwen embedding model and verify missing or invalid API keys return clear errors
- [x] 2.3 Implement job creation with Excel upload, run mode, thresholds, delay, batch preference, and topic fields, then verify it returns a job id
- [x] 2.4 Implement background job execution using existing progress and cancellation callbacks, then verify job state records progress, logs, completion, errors, and output path
- [x] 2.5 Implement `GET /api/jobs/{job_id}` and verify active, completed, failed, and cancelled jobs return consistent status payloads
- [x] 2.6 Implement `POST /api/jobs/{job_id}/cancel` and verify cancellation stops an active job without exposing a completed download
- [x] 2.7 Implement `GET /api/jobs/{job_id}/download` and verify completed jobs download the generated Excel file while incomplete jobs are rejected

## 3. Frontend Web App

- [x] 3.1 Create the React + Vite + TypeScript frontend structure and verify the dev server starts
- [x] 3.2 Build the primary scoring screen with API key entry, file upload, output/job controls, run mode selection, thresholds, delay, batch preference, and topic input, verified visually in desktop and mobile-sized viewports
- [x] 3.3 Display fixed provider/model information as read-only content and verify no editable provider/model controls exist
- [x] 3.4 Connect API key testing to `POST /api/config/test` and verify success and failure states render clearly
- [x] 3.5 Connect job creation, status polling, cancellation, logs, progress display, and download actions, verified against the local backend
- [x] 3.6 Ensure controls reflect job state by disabling conflicting actions during active runs and re-enabling valid actions after completion, failure, or cancellation

## 4. Documentation And Validation

- [x] 4.1 Update README setup instructions for backend and frontend dependency installation and verify commands are copy-paste runnable
- [x] 4.2 Document the fixed Qwen/DashScope configuration, single API key requirement, and `text-embedding-v4` batch handling
- [x] 4.3 Document the local web workflow for testing the key, uploading an Excel file, running each mode, cancelling, and downloading results
- [x] 4.4 Run backend syntax/tests and frontend build/check commands and record results
- [x] 4.5 Run `openspec validate replace-tkinter-with-qwen-web-app --strict` and verify the change passes
