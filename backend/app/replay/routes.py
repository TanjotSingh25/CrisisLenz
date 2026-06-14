from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.enums import SourceType
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


@router.post("/reseed", response_model=MessageResponse)
def reseed_replay(db: Session = Depends(get_db)):
    """
    Wipe replay_signals and reload from the committed JSON files.
    Use this to fix duplicates or restore a clean dataset.
    Existing ai_analyses and events are kept but unlinked from signals.
    """
    counts = service.reseed_all(db)
    return MessageResponse(
        message=f"Reseeded: {counts['wikinews']} Wikinews + {counts['eonet']} EONET = {counts['total']} total signals."
    )


@router.get("/status", response_model=StatusResponse)
def replay_status(db: Session = Depends(get_db)):
    return service.get_status(db)


@router.post("/next", response_model=ReplaySignalOut)
def release_next(
    source_type: SourceType | None = Query(default=None, description="Filter by source_type (e.g. eonet_event, wikinews_dump)"),
    db: Session = Depends(get_db),
):
    return service.release_next(db, source_type=source_type)


@router.post("/release/{signal_id}", response_model=ReplaySignalOut)
def release_specific(signal_id: int, db: Session = Depends(get_db)):
    """Release one specific signal by id — lets the demo pick a known article/event."""
    return service.release_specific(db, signal_id)


@router.get("/signals/released", response_model=list[ReplaySignalOut])
def list_released(
    source_type: SourceType | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.get_signals_by_status(db, "released", source_type=source_type)


@router.get("/signals/pending", response_model=list[ReplaySignalOut])
def list_pending(
    source_type: SourceType | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return service.get_signals_by_status(db, "pending", source_type=source_type)


@router.post("/release-and-analyze", response_model=AnalysisResponse)
def release_and_analyze(
    source_type: SourceType | None = Query(default=None, description="Release from this source_type specifically"),
    db: Session = Depends(get_db),
):
    """
    One-button demo endpoint: releases the next pending signal and immediately
    runs it through the Gemini analysis pipeline.

    This is how the simulator feeds the real product in the demo.
    In production this step wouldn't exist — signals would arrive live.
    """
    signal = service.release_next(db, source_type=source_type)
    try:
        signal_dict = processing.replay_signal_to_dict(signal)
        return processing.ingest_signal(db, signal_dict, replay_signal=signal)
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@router.post("/reset", response_model=MessageResponse)
def reset_replay(
    source_type: SourceType | None = Query(default=None, description="Reset only this source_type. Omit to reset all."),
    db: Session = Depends(get_db),
):
    count = service.reset_signals(db, source_type=source_type)
    label = f"source_type='{source_type.value}'" if source_type else "all sources"
    return MessageResponse(message=f"Reset {count} signals to pending ({label}).")
