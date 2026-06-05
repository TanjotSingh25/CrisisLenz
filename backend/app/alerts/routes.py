from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.alerts import service
from app.alerts.schemas import (
    AlertOut,
    AlertSummaryResponse,
    GenerateForEventResponse,
    GeneratePendingResponse,
)
from app.database import get_db
from app.replay.schemas import MessageResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/generate-for-event/{event_id}", response_model=GenerateForEventResponse)
def generate_for_event(event_id: int, db: Session = Depends(get_db)):
    """Create client alerts from this event's impact matches. Skips duplicates."""
    return service.generate_for_event(db, event_id)


@router.post("/generate-pending", response_model=GeneratePendingResponse)
def generate_pending(db: Session = Depends(get_db)):
    """Create alerts for every impact match that doesn't have one yet."""
    return service.generate_pending(db)


@router.get("/summary", response_model=AlertSummaryResponse)
def alerts_summary(db: Session = Depends(get_db)):
    """Counts by status and by risk level — useful for the future dashboard."""
    return service.get_summary(db)


@router.get("", response_model=list[AlertOut])
def list_alerts(
    status: str | None = Query(default=None),
    client_id: int | None = Query(default=None),
    event_id: int | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """List alerts, optionally filtered by status, client, event, or risk level."""
    return service.list_alerts(db, status, client_id, event_id, risk_level)


@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(alert_id: int, db: Session = Depends(get_db)):
    """Retrieve a single alert by id."""
    return service.get_alert(db, alert_id)


@router.post("/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as acknowledged (new -> acknowledged)."""
    return service.acknowledge_alert(db, alert_id)


@router.post("/{alert_id}/dismiss", response_model=AlertOut)
def dismiss_alert(alert_id: int, db: Session = Depends(get_db)):
    """Mark an alert as dismissed (-> dismissed). The alert is kept, not deleted."""
    return service.dismiss_alert(db, alert_id)


@router.delete("/clear", response_model=MessageResponse)
def clear_alerts(db: Session = Depends(get_db)):
    """Delete all alerts and reset the ID sequence. Use to start fresh."""
    service.clear_all_alerts(db)
    return MessageResponse(message="Cleared all alerts and reset ID sequence.")

