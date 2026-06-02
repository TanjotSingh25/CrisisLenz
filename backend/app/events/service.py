from sqlalchemy.orm import Session

from app.ai.schemas import SignalAnalysisResult
from app.config import settings
from app.events.models import AiAnalysis, Event


def create_ai_analysis(
    db: Session,
    replay_signal_id: int | None,
    result: SignalAnalysisResult,
    prompt_version: str,
) -> AiAnalysis:
    analysis = AiAnalysis(
        replay_signal_id=replay_signal_id,
        model_name=settings.gemini_model,
        prompt_version=prompt_version,
        is_event_worthy=result.is_event_worthy,
        rejection_reason=result.rejection_reason,
        event_type=result.event_type,
        severity=result.severity,
        confidence=result.confidence,
        title=result.title,
        summary=result.summary,
        location_name=result.location_name,
        latitude=result.latitude,
        longitude=result.longitude,
        business_impact=result.business_impact,
        recommended_action=result.recommended_action,
        reasoning_brief=result.reasoning_brief,
        raw_response_json=result.model_dump(),
    )
    db.add(analysis)
    db.flush()
    return analysis


def create_event(
    db: Session,
    replay_signal_id: int | None,
    analysis: AiAnalysis,
    result: SignalAnalysisResult,
) -> Event:
    event = Event(
        replay_signal_id=replay_signal_id,
        ai_analysis_id=analysis.id,
        event_type=result.event_type,
        title=result.title,
        summary=result.summary,
        severity=result.severity,
        confidence=result.confidence,
        location_name=result.location_name,
        latitude=result.latitude,
        longitude=result.longitude,
        business_impact=result.business_impact,
        recommended_action=result.recommended_action,
        status="active",
    )
    db.add(event)
    db.flush()
    return event


def get_events(db: Session, limit: int = 50, offset: int = 0) -> list[Event]:
    return (
        db.query(Event)
        .order_by(Event.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


def get_event_by_id(db: Session, event_id: int) -> Event | None:
    return db.query(Event).filter(Event.id == event_id).first()


def get_analysis_by_id(db: Session, analysis_id: int) -> AiAnalysis | None:
    return db.query(AiAnalysis).filter(AiAnalysis.id == analysis_id).first()
