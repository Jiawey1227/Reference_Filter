from types import SimpleNamespace
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
        store_patch = patch("backend.app.credentials.load_key", return_value="")
        store_patch.start()
        self.addCleanup(store_patch.stop)
        job_manager.jobs.clear()
        self.tmp = tempfile.TemporaryDirectory()
        job_manager.jobs_dir = Path(self.tmp.name)
        job_manager.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.client = TestClient(app)

    def tearDown(self):
        self.tmp.cleanup()

    def test_saved_key_is_used_without_exposing_it(self):
        with patch("backend.app.credentials.load_key", return_value="secret-key"), patch("backend.app.validate_qwen_connection") as validate:
            status = self.client.get("/api/config/credential")
            self.assertEqual(status.json(), {"saved": True})
            response = self.client.post("/api/config/test", json={"api_key": ""})
            self.assertEqual(response.status_code, 200)
            validate.assert_called_once_with("secret-key")
            self.assertNotIn("secret-key", response.text)

    def test_save_and_forget_key(self):
        with patch("backend.app.credentials.save_key") as save, patch("backend.app.credentials.clear_key") as clear:
            self.assertEqual(self.client.post("/api/config/credential", json={"api_key": "secret"}).status_code, 400)
            response = self.client.post("/api/config/credential", json={"api_key": "secret"}, headers={"X-Credential-Action": "save"})
            self.assertEqual(response.json(), {"saved": True})
            save.assert_called_once_with("secret")
            self.assertEqual(self.client.delete("/api/config/credential", headers={"X-Credential-Action": "delete"}).json(), {"saved": False})
            clear.assert_called_once()

    def test_continue_reuses_scored_file_and_original_settings(self):
        path = Path(self.tmp.name) / "scores.xlsx"
        path.write_bytes(b"scored workbook")
        source = SimpleNamespace(status="completed", run_mode="embedding_only", output_path=path,
                                 api_key="original-key", topic="original scope",
                                 affiliation_enabled=True, affiliation_keywords="cardiology")
        def create(**kwargs):
            self.assertEqual(kwargs["upload_file"].read(), b"scored workbook")
            self.assertEqual(kwargs["run_mode"], "llm_only")
            self.assertEqual(kwargs["topic"], "original scope")
            self.assertEqual(kwargs["llm_min_score"], 0.4464)
            self.assertEqual(kwargs["llm_max_score"], 0.4582)
            self.assertEqual(kwargs["api_key"], "original-key")
            return SimpleNamespace(public=lambda: {"id": "next"})
        with patch.object(job_manager, "get", return_value=source), patch.object(job_manager, "create_job", side_effect=create):
            response = self.client.post("/api/jobs/source/continue", json={"lower": .4464, "upper": .4582})
            self.assertEqual(response.json(), {"id": "next"})
            self.assertEqual(self.client.post("/api/jobs/source/continue", json={"lower": .5, "upper": .4}).status_code, 400)
            source.status = "running"
            self.assertEqual(self.client.post("/api/jobs/source/continue", json={"lower": .4464, "upper": .4582}).status_code, 409)

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

    def test_rejects_invalid_screening_settings(self):
        for settings in ({"llm_min_score": "nan"}, {"affiliation_enabled": "true", "affiliation_keywords": " "}):
            response = self.client.post("/api/jobs", data={"api_key": "key", "topic": "heart", **settings}, files={"file": ("input.xlsx", b"input")})
            self.assertEqual(response.status_code, 400)

    def test_job_lifecycle_and_download(self):
        def fake_score(**kwargs):
            self.assertTrue(kwargs["affiliation_enabled"])
            self.assertEqual(kwargs["affiliation_keywords"], "cardiology")
            Path(kwargs["output_file"]).write_bytes(b"result")
            kwargs["progress_callback"](100, "done", done=True)
            return kwargs["output_file"]

        with patch("backend.jobs.qwen_ai_score_ref_column", side_effect=fake_score):
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
                    "affiliation_enabled": "true",
                    "affiliation_keywords": "cardiology",
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
                    "affiliation_enabled": "true",
                    "affiliation_keywords": "cardiology",
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
