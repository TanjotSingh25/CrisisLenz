from datetime import datetime

from pydantic import BaseModel


class ReplaySignalOut(BaseModel):
    id: int
    source_type: str | None
    source_name: str | None
    title: str | None
    published_at: datetime | None
    summary: str | None
    language: str | None
    url: str | None
    filter_score: float | None
    category_hint: str | None
    matched_keywords: list | None
    status: str
    release_order: int | None
    released_at: datetime | None
    processed_at: datetime | None
    latitude: float | None
    longitude: float | None
    event_category: str | None
    event_status: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SourceTypeStatusCounts(BaseModel):
    pending: int = 0
    released: int = 0
    processed: int = 0
    rejected: int = 0


class StatusResponse(BaseModel):
    total: int
    pending: int
    released: int
    processed: int
    rejected: int
    by_source_type: dict[str, SourceTypeStatusCounts] = {}


class LoadEonetRequest(BaseModel):
    snapshot_filename: str | None = None
    replace_existing: bool = True


class LoadResponse(BaseModel):
    loaded: int


class MessageResponse(BaseModel):
    message: str
