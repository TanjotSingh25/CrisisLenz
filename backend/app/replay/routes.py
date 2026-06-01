from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.replay import service
from app.replay.schemas import (
    LoadEonetRequest,
    LoadRequest,
    LoadResponse,
    MessageResponse,
    ReplaySignalOut,
    StatusResponse,
)

router = APIRouter(prefix="/replay", tags=["replay"])


@router.post("/load", response_model=LoadResponse)
def load_replay(body: LoadRequest = LoadRequest(), db: Session = Depends(get_db)):
    count = service.load_signals(db, reset_existing=body.reset_existing)
    return LoadResponse(loaded=count)


@router.post("/load-eonet", response_model=LoadResponse)
def load_eonet(body: LoadEonetRequest = LoadEonetRequest(), db: Session = Depends(get_db)):
    from app.providers.eonet import normalizer, snapshot_service

    filename = body.snapshot_filename or snapshot_service.latest_snapshot()
    if not filename:
        raise HTTPException(
            status_code=404,
            detail="No EONET snapshots found. Fetch one first via POST /eonet/fetch-snapshot.",
        )

    try:
        raw_data = snapshot_service.load_snapshot(filename)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    events = raw_data.get("events", [])
    normalized = [normalizer.normalize_event(e) for e in events]
    count = service.load_eonet_signals(db, normalized, replace_existing=body.replace_existing)
    return LoadResponse(loaded=count)


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
def reset_replay(db: Session = Depends(get_db)):
    count = service.reset_all(db)
    return MessageResponse(message=f"Reset {count} signals to pending.")


@router.delete("/clear", response_model=MessageResponse)
def clear_replay(db: Session = Depends(get_db)):
    count = service.clear_all(db)
    return MessageResponse(message=f"Cleared {count} signals from the table.")
