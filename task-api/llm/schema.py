"""The shape the endpoint promises. Nothing leaves without passing through here."""
from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    feature = "feature"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TriageIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class Triage(BaseModel):
    # Enums, not plain strings. "urgent" or "Billing" is a failure, not a value
    # to shrug at -- a category outside the list is exactly the mistake a model
    # makes and exactly the one that breaks whatever reads this downstream.
    category: Category
    urgency: Urgency
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=200)

    model_config = {"extra": "forbid"}  # an extra field is a failure too
