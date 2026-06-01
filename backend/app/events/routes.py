from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.errors import not_found
from app.database import get_db
from app.events import service
from app.events.schemas import AiAnalysisOut, EventOut

router = APIRouter(tags=["events"])


@router.get("/events", response_model=list[EventOut])
def list_events(
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    return service.get_events(db, limit=limit, offset=offset)


@router.get("/events/{event_id}", response_model=EventOut)
def get_event(event_id: int, db: Session = Depends(get_db)):
    event = service.get_event_by_id(db, event_id)
    if not event:
        raise not_found(f"Event {event_id} not found.")
    return event


@router.get("/ai/analysis/{analysis_id}", response_model=AiAnalysisOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    analysis = service.get_analysis_by_id(db, analysis_id)
    if not analysis:
        raise not_found(f"Analysis {analysis_id} not found.")
    return analysis
