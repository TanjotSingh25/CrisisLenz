from typing import Literal
from pydantic import BaseModel, Field


class SignalAnalysisResult(BaseModel):
    is_event_worthy: bool
    rejection_reason: str | None = None
    event_type: str
    severity: Literal["low", "medium", "high", "critical", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    title: str | None = None
    summary: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    business_impact: str | None = None
    recommended_action: str | None = None
    reasoning_brief: str
