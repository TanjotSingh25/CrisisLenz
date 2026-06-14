from pydantic import BaseModel


class SignalAnalysisResult(BaseModel):
    """
    Validated Gemini output. Only `is_event_worthy` is required — every other
    field is nullable because a rejected signal legitimately returns null
    event_type/severity/etc., and live Gemini output varies. Keeping these
    tolerant prevents a correct rejection from crashing validation.
    """
    is_event_worthy: bool
    rejection_reason: str | None = None
    event_type: str | None = None
    severity: str | None = None
    confidence: float | None = None
    title: str | None = None
    summary: str | None = None
    location_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    business_impact: str | None = None
    recommended_action: str | None = None
    reasoning_brief: str | None = None
