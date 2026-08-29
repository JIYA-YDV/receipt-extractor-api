"""One structured log line per model call. Read this to understand what you're spending."""
import json
from datetime import datetime, timezone
from pathlib import Path

_LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "cost.jsonl"


def log_call(
    prompt_version: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    duration_ms: int,
    repair_count: int,
    outcome: str,  # "ok" | "repaired" | "failed" | "timeout"
) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "duration_ms": duration_ms,
        "repair_count": repair_count,
        "outcome": outcome,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")