"""One place that does: kill-switch check → call → parse → validate → repair once → quarantine → cost log."""
import os
import time
from typing import Tuple
from src.llm.client import get_client, get_model
from src.llm.prompt import load_system_prompt, PROMPT_VERSION
from src.llm.parse import parse_and_validate
from src.llm.quarantine import quarantine
from src.llm.cost_log import log_call
from src.llm.retry import call_with_retry
from src.llm.schema import ExtractOutput, Currency
from decimal import Decimal


def _fallback_response() -> ExtractOutput:
    """Returned when LLM_ENABLED=false. Deterministic, always safe."""
    return ExtractOutput(
        merchant=None,
        total=None,
        currency=Currency.UNKNOWN,
        date=None,
        items=[],
        confidence=0.0,
        needs_review=True,
    )


def _is_enabled() -> bool:
    return os.environ.get("LLM_ENABLED", "true").lower() != "false"


def _call_model_once(messages: list) -> tuple[str, int, int]:
    """Single model call. Returns (text, input_tokens, output_tokens)."""
    client = get_client()

    def _do():
        return client.chat.completions.create(
            model=get_model(),
            messages=messages,
            temperature=0.1,
        )

    response = call_with_retry(_do)
    text = response.choices[0].message.content or ""
    usage = response.usage
    in_toks = usage.prompt_tokens if usage else 0
    out_toks = usage.completion_tokens if usage else 0
    return text, in_toks, out_toks


def extract_with_llm(user_text: str) -> Tuple[ExtractOutput, int]:
    """
    Returns (validated_output, repair_count).
    Raises ValueError if validation fails twice — the route turns this into a 422.
    Returns fallback + repair_count=0 when LLM_ENABLED=false.
    """
    # Kill switch
    if not _is_enabled():
        log_call(
            prompt_version=PROMPT_VERSION,
            model=get_model(),
            input_tokens=0,
            output_tokens=0,
            duration_ms=0,
            repair_count=0,
            outcome="disabled",
        )
        return _fallback_response(), 0

    system_prompt = load_system_prompt()
    start = time.perf_counter()
    total_in = total_out = 0

    # Attempt 1
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]
    raw, in1, out1 = _call_model_once(messages)
    total_in += in1
    total_out += out1

    parsed, error = parse_and_validate(raw)
    if parsed is not None:
        log_call(
            prompt_version=PROMPT_VERSION,
            model=get_model(),
            input_tokens=total_in,
            output_tokens=total_out,
            duration_ms=int((time.perf_counter() - start) * 1000),
            repair_count=0,
            outcome="ok",
        )
        return parsed, 0

    # Attempt 2 — repair
    repair_messages = messages + [
        {"role": "assistant", "content": raw},
        {
            "role": "user",
            "content": (
                "Your previous response was rejected for this reason:\n"
                f"{error}\n\n"
                "Return ONLY a corrected JSON object matching the schema. "
                "No explanation. No code fences. No text before or after."
            ),
        },
    ]
    raw2, in2, out2 = _call_model_once(repair_messages)
    total_in += in2
    total_out += out2

    parsed2, error2 = parse_and_validate(raw2)
    duration_ms = int((time.perf_counter() - start) * 1000)

    if parsed2 is not None:
        log_call(
            prompt_version=PROMPT_VERSION,
            model=get_model(),
            input_tokens=total_in,
            output_tokens=total_out,
            duration_ms=duration_ms,
            repair_count=1,
            outcome="repaired",
        )
        return parsed2, 1

    # Both failed
    quarantine(
        input_text=user_text,
        raw_output=f"ATTEMPT1: {raw}\n---\nATTEMPT2: {raw2}",
        error=f"first={error} | second={error2}",
        prompt_version=PROMPT_VERSION,
    )
    log_call(
        prompt_version=PROMPT_VERSION,
        model=get_model(),
        input_tokens=total_in,
        output_tokens=total_out,
        duration_ms=duration_ms,
        repair_count=1,
        outcome="failed",
    )
    raise ValueError(f"Model output failed validation twice. Last error: {error2}")