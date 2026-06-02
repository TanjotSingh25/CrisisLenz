import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.schemas import AnalysisResponse
from app.replay.models import ReplaySignal
from app.signals import processing

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ai"])

_ALREADY_ANALYZED = {"processed", "rejected", "failed"}


@router.post("/analyze-signal/{signal_id}", response_model=AnalysisResponse)
def analyze_signal(signal_id: int, db: Session = Depends(get_db)):
    """
    Debug/utility endpoint: analyze a specific signal from the simulator DB by ID.
    Use POST /signals/ingest for the production-style path.
    """
    signal = db.query(ReplaySignal).filter(ReplaySignal.id == signal_id).first()
    if not signal:
        raise HTTPException(status_code=404, detail=f"Signal {signal_id} not found.")
    if signal.status == "pending":
        raise HTTPException(status_code=422, detail="Signal not released yet. Call POST /replay/next first.")
    if signal.status in _ALREADY_ANALYZED:
        raise HTTPException(
            status_code=409,
            detail=f"Signal {signal_id} is already {signal.status}.",
        )
    signal_dict = processing.replay_signal_to_dict(signal)
    return processing.ingest_signal(db, signal_dict, replay_signal=signal)


@router.post("/analyze-next-released", response_model=AnalysisResponse)
def analyze_next_released(db: Session = Depends(get_db)):
    """
    Debug/utility endpoint: finds the oldest released-but-unanalyzed signal and processes it.
    Use POST /replay/release-and-analyze for the clean one-button demo path.
    """
    signal = (
        db.query(ReplaySignal)
        .filter(ReplaySignal.status == "released")
        .order_by(ReplaySignal.release_order)
        .first()
    )
    if not signal:
        raise HTTPException(
            status_code=404,
            detail="No released signals waiting. Call POST /replay/next or POST /replay/release-and-analyze.",
        )
    signal_dict = processing.replay_signal_to_dict(signal)
    return processing.ingest_signal(db, signal_dict, replay_signal=signal)
