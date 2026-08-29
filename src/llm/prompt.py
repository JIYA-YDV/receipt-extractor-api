"""Load the versioned prompt file from disk."""
from pathlib import Path

PROMPT_VERSION = "extract-v1"
_PROMPT_PATH = Path(__file__).parent.parent.parent / "prompts" / f"{PROMPT_VERSION}.md"


def load_system_prompt() -> str:
    """Read the prompt file. Cached in memory on first call."""
    return _PROMPT_PATH.read_text(encoding="utf-8")