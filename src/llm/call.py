"""One place that does: call → parse → validate → repair once → quarantine."""
from typing import Tuple
from src.llm.client import get_client, get_model
from src.llm.prompt import load_system_prompt, PROMPT_VERSION
from src.llm.parse import parse_and_validate
from src.llm.quarantine import quarantine
from src.llm.schema import ExtractOutput


def _call_model(messages: list, temperature: float = 0.1) -> str:
    client = get_client()
    response = client.chat.completions.create(
        model=get_model(),
        messages=messages,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def extract_with_llm(user_text: str) -> Tuple[ExtractOutput, int]:
    """
    Returns (validated_output, repair_count).
    Raises ValueError if both attempts fail — the route turns this into a 422.
    """
    system_prompt = load_system_prompt()

    # Attempt 1
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_text},
    ]
    raw = _call_model(messages)
    parsed, error = parse_and_validate(raw)
    if parsed is not None:
        return parsed, 0

    # Attempt 2 — repair. Hand the model its own error.
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
    raw2 = _call_model(repair_messages)
    parsed2, error2 = parse_and_validate(raw2)
    if parsed2 is not None:
        return parsed2, 1

    # Both attempts failed — quarantine and raise
    quarantine(
        input_text=user_text,
        raw_output=f"ATTEMPT1: {raw}\n---\nATTEMPT2: {raw2}",
        error=f"first={error} | second={error2}",
        prompt_version=PROMPT_VERSION,
    )
    raise ValueError(f"Model output failed validation twice. Last error: {error2}")