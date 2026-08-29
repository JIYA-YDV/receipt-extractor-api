"""POST /extract route."""
import os
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.llm.schema import ExtractOutput, Currency
from src.llm.call import extract_with_llm

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


@router.post("/extract", response_model=ExtractOutput)
async def extract(payload: ExtractInput) -> ExtractOutput:
    if os.environ.get("LLM_STUB") == "1":
        return _stub_response()

    try:
        result, _repair_count = extract_with_llm(payload.text)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "model_output_invalid",
                "message": str(e),
                "hint": "The model produced output that could not be validated after one repair attempt. See logs/quarantine.jsonl.",
            },
        )