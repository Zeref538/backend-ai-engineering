"""What a finished record must look like. A web page is untrusted input.

Validation is the gate between "I scraped something" and "I can store this".
Anything that fails is set aside with a reason, never silently dropped.
"""
from pydantic import BaseModel, Field, HttpUrl, field_validator

RATINGS = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class Book(BaseModel):
    title: str = Field(min_length=1)
    product_url: HttpUrl
    price_text: str
    price_gbp: float = Field(gt=0)
    availability_text: str
    in_stock: bool
    rating_text: str
    rating: int = Field(ge=1, le=5)
    description: str | None = None      # some books genuinely have none
    source_page: HttpUrl
    fetched_at: str

    @field_validator("rating_text")
    @classmethod
    def known_rating(cls, v):
        if v not in RATINGS:
            raise ValueError(f"unknown rating word {v!r}")
        return v


def normalize(raw: dict) -> dict:
    """Raw page text in, clean values out. Keeps the originals alongside."""
    price_text = (raw.get("price_text") or "").strip()
    # Strip everything that isn't a digit or a dot: "£51.77" -> "51.77".
    digits = "".join(c for c in price_text if c.isdigit() or c == ".")
    avail = raw.get("availability_text") or ""
    return {
        **raw,
        "price_gbp": float(digits) if digits else None,
        "in_stock": "in stock" in avail.lower(),
        "rating": RATINGS.get(raw.get("rating_text"), None),
    }
