"""POST /extract route. Input validation happens before any model call."""
import os
from decimal import Decimal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from src.llm.schema import ExtractOutput, Currency

router = APIRouter()


class ExtractInput(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    model_config = {"extra": "forbid"}


def _stub_response() -> ExtractOutput:
    """Deterministic response used when LLM_STUB=1. Satisfies the schema."""
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

    raise HTTPException(status_code=501, detail="Model call not implemented yet")