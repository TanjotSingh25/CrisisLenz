from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.replay import service
from app.replay.schemas import (
    MessageResponse,
    ReplaySignalOut,
    StatusResponse,
)

router = APIRouter(prefix="/replay", tags=["replay"])


@router.get("/status", response_model=StatusResponse)
def replay_status(db: Session = Depends(get_db)):
    return service.get_status(db)


@router.post("/next", response_model=ReplaySignalOut)
def release_next(
    source_type: str | None = Query(default=None, description="Filter by source_type (e.g. eonet_event, wikinews_dump)"),
    db: Session = Depends(get_db),
):
    return service.release_next(db, source_type=source_type)


@router.get("/signals/released", response_model=list[ReplaySignalOut])
def list_released(
    source_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.get_signals_by_status(db, "released", source_type=source_type)


@router.get("/signals/pending", response_model=list[ReplaySignalOut])
def list_pending(
    source_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.get_signals_by_status(db, "pending", source_type=source_type)


@router.post("/reset", response_model=MessageResponse)
def reset_replay(
    source_type: str | None = Query(default=None, description="Reset only this source_type. Omit to reset all."),
    db: Session = Depends(get_db),
):
    count = service.reset_signals(db, source_type=source_type)
    label = f"source_type='{source_type}'" if source_type else "all sources"
    return MessageResponse(message=f"Reset {count} signals to pending ({label}).")
