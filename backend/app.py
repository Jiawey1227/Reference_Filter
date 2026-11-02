from __future__ import annotations

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing_extensions import Annotated

from main import AuthenticationError, APIConnectionError, APIError, normalize_api_key, validate_qwen_connection

from screening import validate_settings
from . import credentials
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


def resolve_key(value):
    clean = normalize_api_key(value)
    if clean:
        return clean
    try:
        return credentials.load_key()
    except Exception:
        raise HTTPException(status_code=503, detail="Cannot access the system credential store. Enter your API key manually.") from None


@app.get("/api/config/credential")
def credential_status():
    try:
        return {"saved": bool(credentials.load_key())}
    except Exception:
        raise HTTPException(status_code=503, detail="Cannot access the system credential store.") from None


@app.post("/api/config/credential")
def save_credential(payload: ApiKeyPayload, x_credential_action: str = Header(default="")):
    if x_credential_action != "save":
        raise HTTPException(status_code=400, detail="Invalid credential action")
    key = normalize_api_key(payload.api_key)
    if not key:
        raise HTTPException(status_code=400, detail="Enter an API key to save")
    try:
        credentials.save_key(key)
    except Exception:
        raise HTTPException(status_code=503, detail="Could not save the key in the system credential store.") from None
    return {"saved": True}


@app.delete("/api/config/credential")
def delete_credential(x_credential_action: str = Header(default="")):
    if x_credential_action != "delete":
        raise HTTPException(status_code=400, detail="Invalid credential action")
    try:
        credentials.clear_key()
    except Exception:
        raise HTTPException(status_code=503, detail="Could not remove the saved API key.") from None
    return {"saved": False}


@app.get("/api/provider")
def provider_info():
    return PROVIDER_INFO


@app.post("/api/config/test")
def test_config(payload: ApiKeyPayload):
    api_key = resolve_key(payload.api_key)
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
    topic: Annotated[str, Form()],
    api_key: Annotated[str, Form()] = "",
    run_mode: Annotated[str, Form()] = "full",
    llm_min_score: Annotated[float, Form()] = 0.25,
    llm_max_score: Annotated[float, Form()] = 0.35,
    affiliation_enabled: Annotated[bool, Form()] = False,
    affiliation_keywords: Annotated[str, Form()] = "",
):
    clean_key = resolve_key(api_key)
    if not clean_key:
        raise HTTPException(status_code=400, detail="API Key is required")
    if run_mode not in {"full", "embedding_only", "llm_only"}:
        raise HTTPException(status_code=400, detail="Invalid run mode")
    if not topic.strip():
        raise HTTPException(status_code=400, detail="Topic is required")
    try:
        validate_settings(llm_min_score, llm_max_score, affiliation_enabled, affiliation_keywords)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    job = job_manager.create_job(
        upload_file=file.file,
        filename=file.filename or "input.xlsx",
        api_key=clean_key,
        topic=topic.strip(),
        run_mode=run_mode,
        batch_size=100,
        delay=0.0,
        llm_min_score=llm_min_score,
        llm_max_score=llm_max_score,
        llm_batch_size=50,
        llm_delay=0.0,
        affiliation_enabled=affiliation_enabled,
        affiliation_keywords=affiliation_keywords,
    )
    return job.public()


class ContinuePayload(BaseModel):
    lower: float
    upper: float


@app.post("/api/jobs/{job_id}/continue")
def continue_job(job_id: str, payload: ContinuePayload):
    source = job_manager.get(job_id)
    if not source:
        raise HTTPException(status_code=404, detail="Original task not found. Please generate scores again.")
    if source.status != "completed" or source.run_mode != "embedding_only" or not source.output_path.exists():
        raise HTTPException(status_code=409, detail="A completed score-generation task is required")
    try:
        validate_settings(payload.lower, payload.upper)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None
    with source.output_path.open("rb") as scored_file:
        job = job_manager.create_job(
            upload_file=scored_file, filename="scores.xlsx", api_key=source.api_key,
            topic=source.topic, run_mode="llm_only", batch_size=100, delay=0.0,
            llm_min_score=payload.lower, llm_max_score=payload.upper,
            llm_batch_size=50, llm_delay=0.0,
            affiliation_enabled=source.affiliation_enabled,
            affiliation_keywords=source.affiliation_keywords,
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
