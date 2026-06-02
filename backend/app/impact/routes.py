from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.impact import service
from app.impact.rules import load_rules
from app.impact.schemas import MatchEventResponse

router = APIRouter(prefix="/impact", tags=["impact"])


@router.post("/match-event/{event_id}", response_model=MatchEventResponse)
def match_event(event_id: int, db: Session = Depends(get_db)):
    """Calculate which client assets fall inside this event's estimated impact zone."""
    try:
        return service.match_event(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/match-unmatched-events", response_model=list[MatchEventResponse])
def match_unmatched_events(db: Session = Depends(get_db)):
    """Run impact matching for all events that have not been matched yet."""
    return service.match_unmatched_events(db)


@router.get("/event/{event_id}", response_model=MatchEventResponse)
def get_event_impacts(event_id: int, db: Session = Depends(get_db)):
    """Retrieve all existing impact matches for an event."""
    try:
        return service.get_event_impacts(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/rules")
def get_impact_rules():
    """Return the loaded impact radius rules (from impact_rules.yaml)."""
    return load_rules()
