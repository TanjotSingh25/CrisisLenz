from datetime import datetime

from pydantic import BaseModel


class AffectedAssetOut(BaseModel):
    impact_id: int
    client: str
    asset: str
    asset_type: str | None
    city: str | None
    country: str | None
    latitude: float
    longitude: float
    criticality: str
    distance_km: float
    impact_radius_km: float
    risk_level: str | None
    match_reason: str | None

    model_config = {"from_attributes": True}


class MatchEventResponse(BaseModel):
    event_id: int
    event_title: str | None
    event_type: str | None
    severity: str | None
    latitude: float | None
    longitude: float | None
    impact_radius_km: float | None
    assets_evaluated: int = 0  # how many client assets were checked — 0 means none are seeded
    nearest_km: float | None = None  # distance to closest asset, even if outside radius
    matches_created: int
    total_matches: int
    skipped: bool = False
    skip_reason: str | None = None
    affected_assets: list[AffectedAssetOut] = []


class EventAssetImpactOut(BaseModel):
    id: int
    event_id: int
    client_id: int
    client_asset_id: int
    distance_km: float
    impact_radius_km: float
    risk_level: str | None
    match_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
