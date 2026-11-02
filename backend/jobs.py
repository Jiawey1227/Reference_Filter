from __future__ import annotations

import shutil
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from main import qwen_ai_score_ref_column

from .config import JOBS_DIR


ACTIVE_STATUSES = {"queued", "running"}
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


@dataclass
class JobState:
    id: str
    input_path: Path
    output_path: Path
    api_key: str
    topic: str
    run_mode: str
    batch_size: int
    delay: float
    llm_min_score: float
    llm_max_score: float
    llm_batch_size: int = 50
    llm_delay: float = 0.0
    affiliation_enabled: bool = False
    affiliation_keywords: str = ""
    status: str = "queued"
    progress: float = 0.0
    message: str = "Queued"
    logs: list[str] = field(default_factory=list)
    error: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    cancel_event: threading.Event = field(default_factory=threading.Event)

    def public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "status": self.status,
            "progress": round(float(self.progress), 2),
            "message": self.message,
            "logs": self.logs[-300:],
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "download_ready": self.status == "completed" and self.output_path.exists(),
        }


class JobManager:
    def __init__(self, jobs_dir: Path = JOBS_DIR):
        self.jobs_dir = jobs_dir
        self.jobs: dict[str, JobState] = {}
        self.lock = threading.Lock()
        self.jobs_dir.mkdir(parents=True, exist_ok=True)

    def create_job(
        self,
        *,
        upload_file,
        filename: str,
        api_key: str,
        topic: str,
        run_mode: str,
        batch_size: int,
        delay: float,
        llm_min_score: float,
        llm_max_score: float,
        llm_batch_size: int = 50,
        llm_delay: float = 0.0,
        affiliation_enabled: bool = False,
        affiliation_keywords: str = "",
    ) -> JobState:
        job_id = uuid.uuid4().hex
        job_dir = self.jobs_dir / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        suffix = Path(filename or "input.xlsx").suffix.lower()
        if suffix not in {".xlsx", ".xls"}:
            suffix = ".xlsx"

        input_path = job_dir / f"input{suffix}"
        output_path = job_dir / "result.xlsx"
        with input_path.open("wb") as out:
            shutil.copyfileobj(upload_file, out)

        job = JobState(
            id=job_id,
            input_path=input_path,
            output_path=output_path,
            api_key=api_key,
            topic=topic,
            run_mode=run_mode,
            batch_size=batch_size,
            delay=delay,
            llm_min_score=llm_min_score,
            llm_max_score=llm_max_score,
            llm_batch_size=llm_batch_size,
            llm_delay=llm_delay,
            affiliation_enabled=affiliation_enabled,
            affiliation_keywords=affiliation_keywords,
        )
        with self.lock:
            self.jobs[job_id] = job

        thread = threading.Thread(target=self._run_job, args=(job,), daemon=True)
        thread.start()
        return job

    def get(self, job_id: str) -> JobState | None:
        with self.lock:
            return self.jobs.get(job_id)

    def cancel(self, job_id: str) -> JobState | None:
        job = self.get(job_id)
        if not job:
            return None
        if job.status in ACTIVE_STATUSES:
            job.cancel_event.set()
            self._update(job, message="Cancellation requested")
        return job

    def _update(
        self,
        job: JobState,
        *,
        status: str | None = None,
        progress: float | None = None,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        if status:
            job.status = status
        if progress is not None:
            job.progress = max(0.0, min(100.0, float(progress)))
        if message:
            job.message = message
            job.logs.append(message)
        if error:
            job.error = error
            job.logs.append(error)
        job.updated_at = datetime.now().isoformat(timespec="seconds")

    def _run_job(self, job: JobState) -> None:
        self._update(job, status="running", progress=0, message="Job started")

        def progress_callback(progress, status, done=False):
            self._update(job, progress=progress, message=status)
            if done:
                self._update(job, progress=100, message=status)

        def cancel_check():
            return job.cancel_event.is_set()

        try:
            embedding_only = job.run_mode == "embedding_only"
            llm_only = job.run_mode == "llm_only"
            result = qwen_ai_score_ref_column(
                input_file=str(job.input_path),
                output_file=str(job.output_path),
                api_key=job.api_key,
                topic=job.topic,
                batch_size=job.batch_size,
                delay=job.delay,
                llm_auto_exclude_threshold=job.llm_min_score,
                llm_score_threshold=job.llm_max_score,
                llm_batch_size=job.llm_batch_size,
                llm_delay=job.llm_delay,
                embedding_only=embedding_only,
                llm_only=llm_only,
                progress_callback=progress_callback,
                cancel_check=cancel_check,
                affiliation_enabled=job.affiliation_enabled,
                affiliation_keywords=job.affiliation_keywords,
            )

            if job.cancel_event.is_set() or result is None:
                self._update(job, status="cancelled", message="Job cancelled")
                return

            self._update(job, status="completed", progress=100, message="Job completed")
        except Exception as exc:
            self._update(job, status="failed", error=str(exc), message="Job failed")


job_manager = JobManager()
