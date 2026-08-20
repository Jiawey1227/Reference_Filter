import io
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from backend.jobs import JobManager


class BackendJobManagerTests(unittest.TestCase):
    def test_job_completes_and_exposes_download_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = JobManager(Path(tmp))

            def fake_score(**kwargs):
                Path(kwargs["output_file"]).write_bytes(b"result")
                kwargs["progress_callback"](100, "done", done=True)
                return kwargs["output_file"]

            with patch("backend.jobs.qwen_ai_score_ref_column", side_effect=fake_score), patch(
                "backend.jobs.highlight_countries"
            ):
                job = manager.create_job(
                    upload_file=io.BytesIO(b"input"),
                    filename="input.xlsx",
                    api_key="key",
                    topic="topic",
                    run_mode="full",
                    batch_size=100,
                    delay=0,
                    llm_min_score=0.25,
                    llm_max_score=0.35,
                )
                self._wait_for(lambda: manager.get(job.id).status == "completed")

            public = manager.get(job.id).public()
            self.assertEqual(public["status"], "completed")
            self.assertTrue(public["download_ready"])
            self.assertEqual(public["progress"], 100)

    def test_job_can_be_cancelled(self):
        with tempfile.TemporaryDirectory() as tmp:
            manager = JobManager(Path(tmp))

            def fake_score(**kwargs):
                kwargs["progress_callback"](10, "started")
                for _ in range(50):
                    if kwargs["cancel_check"]():
                        return None
                    time.sleep(0.01)
                return kwargs["output_file"]

            with patch("backend.jobs.qwen_ai_score_ref_column", side_effect=fake_score):
                job = manager.create_job(
                    upload_file=io.BytesIO(b"input"),
                    filename="input.xlsx",
                    api_key="key",
                    topic="topic",
                    run_mode="embedding_only",
                    batch_size=100,
                    delay=0,
                    llm_min_score=0.25,
                    llm_max_score=0.35,
                )
                manager.cancel(job.id)
                self._wait_for(lambda: manager.get(job.id).status == "cancelled")

            public = manager.get(job.id).public()
            self.assertEqual(public["status"], "cancelled")
            self.assertFalse(public["download_ready"])

    def _wait_for(self, predicate, timeout=3):
        deadline = time.time() + timeout
        while time.time() < deadline:
            if predicate():
                return
            time.sleep(0.02)
        self.fail("condition was not met before timeout")


if __name__ == "__main__":
    unittest.main()
