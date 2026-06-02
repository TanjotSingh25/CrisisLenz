from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.events.schemas import AnalysisResponse
from app.signals import processing
from app.signals.schemas import IngestSignalRequest

router = APIRouter(prefix="/signals", tags=["signals"])


@router.post("/ingest", response_model=AnalysisResponse)
def ingest_signal(body: IngestSignalRequest, db: Session = Depends(get_db)):
    """
    Primary entry point for the Crisis Lens analysis pipeline.

    Accepts any signal payload and runs it through Gemini analysis.
    No simulator database lookup — works from any source.

    In the demo: feed this the JSON returned by POST /replay/next.
    In production: a live API connector would call this directly.
    """
    return processing.ingest_signal(db, body.model_dump(), replay_signal=None)
