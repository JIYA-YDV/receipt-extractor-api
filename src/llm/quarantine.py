"""Write failed model outputs to a jsonl file so we can inspect them later."""
import json
from datetime import datetime, timezone
from pathlib import Path

_LOG_PATH = Path(__file__).parent.parent.parent / "logs" / "quarantine.jsonl"


def quarantine(input_text: str, raw_output: str, error: str, prompt_version: str) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_version": prompt_version,
        "error": error,
        "input_text": input_text[:500],  # truncate to keep log readable
        "raw_output": raw_output[:2000],
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")