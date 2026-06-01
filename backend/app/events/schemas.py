from datetime import datetime

from pydantic import BaseModel


class AiAnalysisOut(BaseModel):
    id: int
    replay_signal_id: int
    model_name: str | None
    prompt_version: str | None
    is_event_worthy: bool
    rejection_reason: str | None
    event_type: str | None
    severity: str | None
    confidence: float | None
    title: str | None
    summary: str | None
    location_name: str | None
    latitude: float | None
    longitude: float | None
    business_impact: str | None
    recommended_action: str | None
    reasoning_brief: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: int
    replay_signal_id: int
    ai_analysis_id: int
    event_type: str | None
    title: str | None
    summary: str | None
    severity: str | None
    confidence: float | None
    location_name: str | None
    latitude: float | None
    longitude: float | None
    business_impact: str | None
    recommended_action: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AnalysisResponse(BaseModel):
    signal_id: int
    outcome: str
    analysis_id: int
    is_event_worthy: bool
    event_type: str | None = None
    severity: str | None = None
    confidence: float | None = None
    title: str | None = None
    event_id: int | None = None
    rejection_reason: str | None = None
