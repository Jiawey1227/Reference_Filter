from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing_extensions import Annotated

from main import AuthenticationError, APIConnectionError, APIError, normalize_api_key, validate_qwen_connection

from .config import PROVIDER_INFO
from .jobs import ACTIVE_STATUSES, job_manager


app = FastAPI(title="AI Literature Scoring Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApiKeyPayload(BaseModel):
    api_key: str


@app.get("/api/provider")
def provider_info():
    return PROVIDER_INFO


@app.post("/api/config/test")
def test_config(payload: ApiKeyPayload):
    api_key = normalize_api_key(payload.api_key)
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
    try:
        validate_qwen_connection(api_key)
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="API Key is invalid or expired") from None
    except APIConnectionError:
        raise HTTPException(status_code=503, detail="Cannot connect to Qwen/DashScope API") from None
    except APIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from None
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    return {"ok": True, "provider": PROVIDER_INFO}


@app.post("/api/jobs")
def create_job(
    file: Annotated[UploadFile, File()],
    api_key: Annotated[str, Form()],
    topic: Annotated[str, Form()],
    run_mode: Annotated[str, Form()] = "full",
    batch_size: Annotated[int, Form()] = 100,
    delay: Annotated[float, Form()] = 0.0,
    llm_min_score: Annotated[float, Form()] = 0.25,
    llm_max_score: Annotated[float, Form()] = 0.35,
    llm_batch_size: Annotated[int, Form()] = 50,
    llm_delay: Annotated[float, Form()] = 0.0,
):
    clean_key = normalize_api_key(api_key)
    if not clean_key:
        raise HTTPException(status_code=400, detail="API Key is required")
    if run_mode not in {"full", "embedding_only", "llm_only"}:
        raise HTTPException(status_code=400, detail="Invalid run mode")
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    if llm_min_score >= llm_max_score:
        raise HTTPException(status_code=400, detail="LLM minimum score must be less than maximum score")
    if batch_size < 1 or llm_batch_size < 1:
        raise HTTPException(status_code=400, detail="Batch sizes must be positive")

    job = job_manager.create_job(
        upload_file=file.file,
        filename=file.filename or "input.xlsx",
        api_key=clean_key,
        topic=topic.strip(),
        run_mode=run_mode,
        batch_size=batch_size,
        delay=delay,
        llm_min_score=llm_min_score,
        llm_max_score=llm_max_score,
        llm_batch_size=llm_batch_size,
        llm_delay=llm_delay,
    )
    return job.public()


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.public()


@app.post("/api/jobs/{job_id}/cancel")
def cancel_job(job_id: str):
    job = job_manager.cancel(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status not in ACTIVE_STATUSES and not job.cancel_event.is_set():
        return job.public()
    return job.public()


@app.get("/api/jobs/{job_id}/download")
def download_job(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status != "completed" or not job.output_path.exists():
        raise HTTPException(status_code=409, detail="Result is not ready")
    return FileResponse(
        path=str(job.output_path),
        filename=f"{job_id}_result.xlsx",
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
