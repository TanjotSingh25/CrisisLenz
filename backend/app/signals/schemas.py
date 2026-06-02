from pydantic import BaseModel


class IngestSignalRequest(BaseModel):
    """
    The stable input contract for the Crisis Lens ingestion pipeline.
    Only title is required — everything else enriches the analysis.
    In production this would be populated by a live API connector.
    In the demo the replay simulator provides all fields.
    """
    source_type: str | None = None
    source_name: str | None = None
    title: str
    published_at: str | None = None
    summary: str | None = None
    body: str | None = None
    language: str | None = "en"
    url: str | None = None
    category_hint: str | None = None
    matched_keywords: list[str] | None = None
    latitude: float | None = None
    longitude: float | None = None
    event_category: str | None = None
    event_status: str | None = None
