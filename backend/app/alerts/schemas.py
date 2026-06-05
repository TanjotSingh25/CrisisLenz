from datetime import datetime

from pydantic import BaseModel


class AlertOut(BaseModel):
    id: int
    event_id: int
    client_id: int
    client_asset_id: int
    event_asset_impact_id: int
    # Friendly names denormalised for display
    client: str | None = None
    asset: str | None = None
    asset_type: str | None = None
    event_title: str | None = None
    event_type: str | None = None
    alert_title: str | None
    alert_summary: str | None
    recommended_action: str | None
    risk_level: str | None
    status: str
    delivery_channel: str
    delivery_status: str
    distance_km: float | None
    impact_radius_km: float | None
    created_at: datetime
    updated_at: datetime
    acknowledged_at: datetime | None
    dismissed_at: datetime | None

    model_config = {"from_attributes": True}


class GeneratedAlertBrief(BaseModel):
    """Compact alert representation used inside generation responses."""
    id: int
    client: str | None
    asset: str | None
    risk_level: str | None
    status: str

    model_config = {"from_attributes": True}


class GenerateForEventResponse(BaseModel):
    event_id: int
    event_title: str | None = None
    impacts_found: int
    alerts_created: int
    alerts_skipped: int
    alerts: list[GeneratedAlertBrief] = []


class GeneratePendingResponse(BaseModel):
    impacts_found: int
    alerts_created: int
    alerts_skipped: int
    alerts: list[GeneratedAlertBrief] = []


class AlertSummaryResponse(BaseModel):
    total: int
    new: int
    acknowledged: int
    dismissed: int
    by_risk_level: dict[str, int]
