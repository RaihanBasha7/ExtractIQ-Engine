"""
Target extraction schema — mirrors PRD Section 9 (Data Requirements) exactly.
This is the strict nested schema that `instructor` enforces against Groq output.
Any deviation (bad enum, wrong type, missing required field) triggers the
Model-Driven Repair Loop in app/extraction.py — never a regex fallback.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    billing = "billing"
    technical = "technical"
    shipping = "shipping"
    account = "account"
    product = "product"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class Sentiment(str, Enum):
    frustrated = "frustrated"
    neutral = "neutral"
    satisfied = "satisfied"
    angry = "angry"


class ResolutionStatus(str, Enum):
    unresolved = "unresolved"
    pending = "pending"
    resolved = "resolved"
    escalated = "escalated"


class Customer(BaseModel):
    name: Optional[str] = Field(
        default=None, description="Customer name if explicitly mentioned in the text, else null."
    )
    account_id: Optional[str] = Field(default=None, description="Account or order ID if mentioned, else null.")


class Issue(BaseModel):
    category: IssueCategory
    subcategory: Optional[str] = Field(
        default=None, description="Free-text subcategory, e.g. 'refund', 'login failure'."
    )
    product_or_service: Optional[str] = Field(default=None, description="Product or service name mentioned, else null.")
    urgency: Urgency


class Entities(BaseModel):
    order_ids: list[str] = Field(default_factory=list)
    dates_mentioned: list[str] = Field(default_factory=list)
    amounts_mentioned: list[str] = Field(default_factory=list)


class TicketExtraction(BaseModel):
    """Strict nested schema — the single source of truth for what 'schema-valid' means."""

    ticket_id: str
    customer: Customer
    issue: Issue
    sentiment: Sentiment
    entities: Entities
    requested_action: Optional[str] = Field(
        default=None, description="What the customer explicitly asked for, else null."
    )
    resolution_status: ResolutionStatus
