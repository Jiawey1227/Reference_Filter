from pathlib import Path

from main import (
    QWEN_BASE_URL,
    QWEN_CACHE_FILE,
    QWEN_EMBEDDING_MAX_BATCH_SIZE,
    QWEN_EMBEDDING_MODEL,
    QWEN_LLM_MODEL,
)


RUNTIME_DIR = Path("runtime")
JOBS_DIR = RUNTIME_DIR / "jobs"

PROVIDER_INFO = {
    "provider": "Qwen / DashScope",
    "base_url": QWEN_BASE_URL,
    "embedding_model": QWEN_EMBEDDING_MODEL,
    "llm_model": QWEN_LLM_MODEL,
    "embedding_max_batch_size": QWEN_EMBEDDING_MAX_BATCH_SIZE,
    "cache_file": QWEN_CACHE_FILE,
}
