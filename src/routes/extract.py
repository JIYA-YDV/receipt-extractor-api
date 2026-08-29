"""POST /extract route."""
import os
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.llm.schema import ExtractOutput, Currency
from src.llm.client import get_client, get_model
from src.llm.prompt import load_system_prompt, PROMPT_VERSION

router = APIRouter()


class ExtractInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    model_config = {"extra": "forbid"}


def _stub_response() -> ExtractOutput:
    return ExtractOutput(
        merchant="STUB CAFE",
        total=Decimal("12.34"),
        currency=Currency.USD,
        date="2024-01-15",
        items=[],
        confidence=0.99,
        needs_review=False,
    )


@router.post("/extract")
async def extract(payload: ExtractInput):
    if os.environ.get("LLM_STUB") == "1":
        return _stub_response()

    client = get_client()
    system_prompt = load_system_prompt()

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": payload.text},  # User content NEVER goes in system prompt
        ],
        temperature=0.1,
    )

    raw_text = response.choices[0].message.content
    # Stage 3 will parse + validate this properly. For now just return it as debug.
    return {"_raw_debug": raw_text, "_prompt_version": PROMPT_VERSION}