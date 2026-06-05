from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class ClientAlert(Base):
    """
    A simulated client-facing alert generated from an event-asset impact match.

    Alerts are created deterministically from existing data (event + client +
    asset + impact match) — no Gemini call here. Delivery is simulated only.
    """

    __tablename__ = "client_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # References — what this alert is about
    event_id: Mapped[int] = mapped_column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    client_id: Mapped[int] = mapped_column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    client_asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("client_assets.id"), nullable=False, index=True)
    event_asset_impact_id: Mapped[int] = mapped_column(Integer, ForeignKey("event_asset_impacts.id"), nullable=False)

    # Alert content (denormalised so the alert reads on its own)
    alert_title: Mapped[str | None] = mapped_column(Text)
    alert_summary: Mapped[str | None] = mapped_column(Text)
    recommended_action: Mapped[str | None] = mapped_column(Text)
    risk_level: Mapped[str | None] = mapped_column(String(20), index=True)

    # Lifecycle: new -> acknowledged / dismissed
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new", index=True)

    # Simulated delivery (no real sending in this module)
    delivery_channel: Mapped[str] = mapped_column(String(50), nullable=False, default="simulated_dashboard")
    delivery_status: Mapped[str] = mapped_column(String(20), nullable=False, default="not_sent")

    # Snapshot of the match geometry at alert time
    distance_km: Mapped[float | None] = mapped_column(Float)
    impact_radius_km: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    dismissed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
