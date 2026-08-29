"""Output schema for the /extract endpoint with robust pre-validation recovery and business rule enforcement."""
import re
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator
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
    """The exact shape returned to the API caller."""
    merchant: Optional[str] = Field(None, max_length=120)
    total: Optional[Decimal] = None
    currency: Currency = Currency.UNKNOWN
    date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    items: List[LineItem] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    needs_review: bool = True

    model_config = {"extra": "forbid"}

    @model_validator(mode="before")
    @classmethod
    def preprocess_llm_output(cls, data):
        """Clean up and format messy LLM output before Pydantic validates it."""
        if not isinstance(data, dict):
            return data

        null_indicators = {"unknown", "n/a", "none", "null", "undefined", "", "banana"}

        # 1. Clean up Merchant
        if "merchant" in data:
            m = data["merchant"]
            if isinstance(m, str) and (m.strip().lower() in null_indicators):
                data["merchant"] = None

        # 2. Convert raw slash dates (MM/DD/YYYY or DD/MM/YYYY) to YYYY-MM-DD
        if "date" in data:
            d = data["date"]
            if isinstance(d, str):
                d_clean = d.strip()
                if d_clean.lower() in null_indicators:
                    data["date"] = None
                else:
                    match = re.match(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$", d_clean)
                    if match:
                        g1, g2, g3 = match.group(1), match.group(2), match.group(3)
                        if int(g1) > 12:
                            data["date"] = f"{g3}-{g2.zfill(2)}-{g1.zfill(2)}"
                        else:
                            data["date"] = f"{g3}-{g1.zfill(2)}-{g2.zfill(2)}"
            else:
                data["date"] = None

        # 3. Clean up items list
        if "items" not in data or data["items"] is None:
            data["items"] = []
        elif isinstance(data["items"], list):
            valid_items = []
            for item in data["items"]:
                if isinstance(item, dict) and item.get("description"):
                    amt = item.get("amount")
                    if isinstance(amt, str) and amt.strip().lower() in null_indicators:
                        item["amount"] = None
                    valid_items.append(item)
            data["items"] = valid_items

        # 4. Normalize Currency string to enum
        if "currency" in data:
            c = data["currency"]
            if c is None or (isinstance(c, str) and c.strip().lower() in null_indicators):
                data["currency"] = "UNKNOWN"
            elif isinstance(c, str):
                c_upper = c.strip().upper()
                if c_upper not in Currency.__members__:
                    data["currency"] = "UNKNOWN"
                else:
                    data["currency"] = c_upper

        # 5. BUSINESS RULE INVARIANT ENFORCEMENT:
        # If any critical field is missing, force needs_review=True and confidence < 0.5
        is_missing_critical = (
            data.get("merchant") is None or
            data.get("total") is None or
            data.get("date") is None
        )

        if is_missing_critical:
            data["needs_review"] = True
            raw_conf = data.get("confidence", 0.3)
            try:
                data["confidence"] = min(float(raw_conf), 0.35)
            except (ValueError, TypeError):
                data["confidence"] = 0.35
        else:
            if "needs_review" not in data or data["needs_review"] is None:
                data["needs_review"] = False
            if "confidence" not in data or data["confidence"] is None:
                data["confidence"] = 0.95
            else:
                try:
                    data["confidence"] = float(data["confidence"])
                except (ValueError, TypeError):
                    data["confidence"] = 0.85

        return data