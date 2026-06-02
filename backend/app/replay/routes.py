from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.schemas import AnalysisResponse
from app.replay import service
from app.replay.schemas import (
    MessageResponse,
    ReplaySignalOut,
    StatusResponse,
)
from app.signals import processing

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


@router.post("/release-and-analyze", response_model=AnalysisResponse)
def release_and_analyze(
    source_type: str | None = Query(default=None, description="Release from this source_type specifically"),
    db: Session = Depends(get_db),
):
    """
    One-button demo endpoint: releases the next pending signal and immediately
    runs it through the Gemini analysis pipeline.

    This is how the simulator feeds the real product in the demo.
    In production this step wouldn't exist — signals would arrive live.
    """
    signal = service.release_next(db, source_type=source_type)
    signal_dict = processing.replay_signal_to_dict(signal)
    return processing.ingest_signal(db, signal_dict, replay_signal=signal)


@router.post("/reset", response_model=MessageResponse)
def reset_replay(
    source_type: str | None = Query(default=None, description="Reset only this source_type. Omit to reset all."),
    db: Session = Depends(get_db),
):
    count = service.reset_signals(db, source_type=source_type)
    label = f"source_type='{source_type}'" if source_type else "all sources"
    return MessageResponse(message=f"Reset {count} signals to pending ({label}).")
