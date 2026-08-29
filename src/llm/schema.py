"""Output schema for the /extract endpoint. Defined once, validated everywhere."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, condecimal
from decimal import Decimal


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"
    JPY = "JPY"
    CAD = "CAD"
    AUD = "AUD"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


class LineItem(BaseModel):
    description: str = Field(..., min_length=1, max_length=120)
    amount: Optional[Decimal] = None


class ExtractOutput(BaseModel):
    """The exact shape returned to the API caller. No extra fields allowed."""
    merchant: Optional[str] = Field(None, max_length=120)
    total: Optional[Decimal] = None
    currency: Currency = Currency.UNKNOWN
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    items: List[LineItem] = Field(default_factory=list)
    confidence: float = Field(..., ge=0.0, le=1.0)
    needs_review: bool

    model_config = {"extra": "forbid"}  # Reject extra fields from the model