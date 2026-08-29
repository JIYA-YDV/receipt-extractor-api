## 2.2 LLM client — `src/llm/client.py`
"""Single OpenAI-compatible client with an explicit timeout."""
import os
from openai import OpenAI

_client: OpenAI | None = None


def get_client() -> OpenAI:
    """Return a cached client. Timeout is set explicitly — never trust the SDK default."""
    global _client
    if _client is None:
        timeout = float(os.environ.get("LLM_TIMEOUT_SECONDS", "30"))
        _client = OpenAI(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ["LLM_API_KEY"],
            timeout=timeout,
            max_retries=0,  # We handle retries ourselves in Stage 4
        )
    return _client


def get_model() -> str:
    return os.environ["LLM_MODEL"]