from pydantic import BaseModel, Field


class IngestSignalRequest(BaseModel):
    """
    The stable input contract for the Crisis Lens ingestion pipeline.
    Only title is required — everything else enriches the analysis.
    In production this would be populated by a live API connector.
    In the demo the replay simulator provides all fields.

    Text fields are length-capped to reject oversized payloads. The body is
    further truncated before being sent to Gemini (see prompt_loader).
    """
    source_type: str | None = Field(default=None, max_length=50)
    source_name: str | None = Field(default=None, max_length=200)
    title: str = Field(min_length=1, max_length=1000)
    published_at: str | None = Field(default=None, max_length=64)
    summary: str | None = Field(default=None, max_length=10_000)
    body: str | None = Field(default=None, max_length=200_000)
    language: str | None = Field(default="en", max_length=16)
    url: str | None = Field(default=None, max_length=2000)
    category_hint: str | None = Field(default=None, max_length=100)
    matched_keywords: list[str] | None = Field(default=None, max_length=100)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    event_category: str | None = Field(default=None, max_length=100)
    event_status: str | None = Field(default=None, max_length=50)
