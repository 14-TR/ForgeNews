from typing import Optional, Literal
from pydantic import BaseModel, Field

class Insight(BaseModel):
    domain: Literal["conflict", "ai", "markets", "global"]
    title: str
    body: str
    source_id: str
    event_date: str  # ISO date
    # --- scores ---
    relevance: float = Field(ge=0, le=1)
    novelty: float = Field(ge=0, le=1)
    volatility: Optional[float] = Field(default=None, ge=0, le=1)  # markets only
    confidence: Literal["low", "medium", "high"] 