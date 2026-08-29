"""Parse model output → validate → repair once if needed."""
import json
import re
from typing import Tuple, Optional
from pydantic import ValidationError
from src.llm.schema import ExtractOutput


CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def strip_code_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers the model sometimes adds."""
    return CODE_FENCE_RE.sub("", text).strip()


def extract_first_json_object(text: str) -> Optional[str]:
    """Find the first {...} JSON object in a string. Handles nested braces."""
    text = strip_code_fences(text)
    start = text.find("{")
    if start == -1:
        return None
    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def parse_and_validate(raw: str) -> Tuple[Optional[ExtractOutput], Optional[str]]:
    """
    Try to parse and validate raw model text.
    Returns (parsed_object, None) on success or (None, error_message) on failure.
    """
    candidate = extract_first_json_object(raw)
    if candidate is None:
        return None, "Response contained no JSON object."

    try:
        data = json.loads(candidate)
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e.msg} at position {e.pos}"

    try:
        return ExtractOutput.model_validate(data), None
    except ValidationError as e:
        return None, f"Schema validation failed: {e}"