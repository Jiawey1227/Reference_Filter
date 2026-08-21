import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app
from backend.jobs import job_manager


class BackendApiTests(unittest.TestCase):
    def setUp(self):
        job_manager.jobs.clear()
        self.tmp = tempfile.TemporaryDirectory()
        job_manager.jobs_dir = Path(self.tmp.name)
        job_manager.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.client = TestClient(app)

    def tearDown(self):
        self.tmp.cleanup()

    def test_provider_and_config_validation(self):
        provider = self.client.get("/api/provider")
        self.assertEqual(provider.status_code, 200)
        self.assertEqual(provider.json()["embedding_model"], "qwen3.7-text-embedding")

        missing = self.client.post("/api/config/test", json={"api_key": ""})
        self.assertEqual(missing.status_code, 400)

        with patch("backend.app.validate_qwen_connection", return_value=True):
            ok = self.client.post("/api/config/test", json={"api_key": "key"})
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.json()["ok"])

    def test_job_lifecycle_and_download(self):
        def fake_score(**kwargs):
            Path(kwargs["output_file"]).write_bytes(b"result")
            kwargs["progress_callback"](100, "done", done=True)
            return kwargs["output_file"]

        with patch("backend.jobs.qwen_ai_score_ref_column", side_effect=fake_score), patch(
            "backend.jobs.highlight_countries"
        ):
            created = self.client.post(
                "/api/jobs",
                data={
                    "api_key": "key",
                    "topic": "topic",
                    "run_mode": "full",
                    "batch_size": "100",
                    "delay": "0",
                    "llm_min_score": "0.25",
                    "llm_max_score": "0.35",
                },
                files={"file": ("input.xlsx", b"content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            self.assertEqual(created.status_code, 200)
            job_id = created.json()["id"]
            self._wait_for(lambda: self.client.get(f"/api/jobs/{job_id}").json()["status"] == "completed")

        status = self.client.get(f"/api/jobs/{job_id}")
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["download_ready"])

        download = self.client.get(f"/api/jobs/{job_id}/download")
        self.assertEqual(download.status_code, 200)
        self.assertEqual(download.content, b"result")

    def test_cancel_endpoint_requests_cancellation(self):
        def slow_score(**kwargs):
            for _ in range(50):
                if kwargs["cancel_check"]():
                    return None
                time.sleep(0.01)
            return kwargs["output_file"]

        with patch("backend.jobs.qwen_ai_score_ref_column", side_effect=slow_score):
            created = self.client.post(
                "/api/jobs",
                data={
                    "api_key": "key",
                    "topic": "topic",
                    "run_mode": "embedding_only",
                    "batch_size": "100",
                    "delay": "0",
                    "llm_min_score": "0.25",
                    "llm_max_score": "0.35",
                },
                files={"file": ("input.xlsx", b"content", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            )
            self.assertEqual(created.status_code, 200)
            job_id = created.json()["id"]
            cancelled = self.client.post(f"/api/jobs/{job_id}/cancel")
            self.assertEqual(cancelled.status_code, 200)
            self._wait_for(lambda: self.client.get(f"/api/jobs/{job_id}").json()["status"] == "cancelled")

        status = self.client.get(f"/api/jobs/{job_id}").json()
        self.assertFalse(status["download_ready"])

    def _wait_for(self, predicate, timeout=3):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return
            time.sleep(0.02)
        self.fail("condition was not met before timeout")


if __name__ == "__main__":
    unittest.main()
