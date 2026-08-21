# AI Literature Scoring Tool

## 1. Project Overview

AI Literature Scoring Tool is a local web application for screening academic references against a research topic or special issue scope.

Users upload an Excel file, enter a research topic, and receive an Excel result file with semantic similarity scores, LLM scope-screening decisions, exclusion flags, and country/email highlighting.

The application is locked to Qwen / DashScope China endpoint:

```text
Base URL: https://dashscope.aliyuncs.com/compatible-mode/v1
Embedding Model: qwen3.7-text-embedding
LLM Model: qwen3.7-flash
Embedding request limit: 10 texts/request
```

Only one DashScope-compatible API Key is required.

## 2. Problem

Manually judging whether a large set of manuscript titles or references matches a research topic is slow, inconsistent, and hard to audit.

Common pain points:

- Large Excel files contain many duplicate or borderline references.
- Keyword matching misses semantic relevance.
- LLM-only screening can be expensive when every row is sent to a chat model.
- Different users may accidentally choose unsupported API providers or model names.
- A desktop Tkinter GUI is less comfortable for repeated workflow use.

## 3. Solution

The tool combines embedding similarity and conservative LLM screening:

1. Generate an embedding for the research topic.
2. Generate embeddings for unique references.
3. Compute cosine similarity and write a `score` column.
4. Keep high-score references automatically.
5. Auto-mark very low-score references as probable out of scope.
6. Send only boundary-score references to Qwen LLM for scope screening.
7. Export a result Excel file with decisions, confidence, reasons, and highlighting.

The Web UI hides provider/model settings so users only need to provide a valid DashScope API Key and input data.

## 4. Demo

Development mode:

```text
http://127.0.0.1:5173
```

Typical workflow:

1. Open the local web app.
2. Enter DashScope API Key.
3. Click "测试连接".
4. Upload an Excel file containing `ref`, `refs`, or `Reference`.
5. Enter the research topic/scope.
6. Choose run mode and thresholds.
7. Click "开始处理".
8. Download the generated result Excel file.

## 5. Workflow / Architecture

```text
Excel upload
    |
    v
FastAPI backend job
    |
    +--> Read and normalize ref/refs/Reference column
    |
    +--> Qwen embedding: qwen3.7-text-embedding
    |       - provider/model-aware cache
    |       - max 10 texts per embedding request
    |
    +--> Cosine similarity scoring
    |
    +--> Threshold routing
    |       - high score: keep
    |       - very low score: probable out of scope
    |       - boundary score: send to LLM
    |
    +--> Qwen LLM: qwen3.7-flash
    |
    +--> Excel output + country/email highlighting
    |
    v
Download result
```

Project structure:

```text
backend/
  app.py          # FastAPI routes
  jobs.py         # background job state and execution
  config.py       # fixed provider information

frontend/
  src/            # React + Vite + TypeScript UI

main.py           # scoring, LLM screening, Excel highlighting
requirements.txt  # Python dependencies
start_web_app.bat # one-click local startup script
```

## 6. Key Features

- Modern local Web UI.
- Fixed Qwen / DashScope China endpoint.
- One API Key for both embedding and LLM.
- Three run modes:
  - Full run: embedding + LLM screening
  - Embedding only: generate `score`
  - LLM only: use existing `score` column
- Provider/model-aware embedding cache.
- Automatic embedding request chunking: max 10 texts/request.
- Background jobs with progress, logs, cancellation, and download.
- Excel output with:
  - `score`
  - `scope_decision`
  - `scope_confidence`
  - `exclude`
  - `screening_reason`
- Country/email highlighting after full or LLM-only processing.

## 7. Tech Stack

Backend:

- Python
- FastAPI
- Uvicorn
- OpenAI-compatible SDK
- pandas
- numpy
- openpyxl

Frontend:

- React
- Vite
- TypeScript
- CSS

AI Provider:

- Qwen / DashScope China endpoint
- `qwen3.7-text-embedding`
- `qwen3.7-flash`

## 8. How to Run

### Install Python Dependencies

```bat
cd C:\Users\MDPI\Documents\work\Workspace\Script
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If Windows system proxy causes pip errors, run:

```bat
set NO_PROXY=*
set no_proxy=*
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### Install Frontend Dependencies

```bat
cd C:\Users\MDPI\Documents\work\Workspace\Script\frontend
npm install
```

### One-Click Startup

Double-click:

```text
start_web_app.bat
```

The script starts:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:5173`

It also opens the frontend in your browser automatically.

Close the two terminal windows opened by the script to stop the app.

### Manual Startup

Backend:

```bat
cd C:\Users\MDPI\Documents\work\Workspace\Script
set NO_PROXY=*
set no_proxy=*
.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

Frontend:

```bat
cd C:\Users\MDPI\Documents\work\Workspace\Script\frontend
npm run dev -- --host 127.0.0.1
```

Open:

```text
http://127.0.0.1:5173
```

Runtime files such as `cache/`, `runtime/`, logs, and generated Excel files should not be committed.
