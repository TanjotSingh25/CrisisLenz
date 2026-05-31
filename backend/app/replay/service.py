import json
from datetime import datetime
from pathlib import Path

from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.common.errors import not_found
from app.common.timestamps import utcnow
from app.replay.models import ReplaySignal

REPLAY_FILE = Path("/app/data/replay/final_replay_signals.json")


def load_signals(db: Session, reset_existing: bool = True) -> int:
    if reset_existing:
        db.query(ReplaySignal).delete()
        db.commit()

    with open(REPLAY_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    signals = []
    for idx, record in enumerate(records):
        published_at = None
        raw_ts = record.get("published_at")
        if raw_ts:
            try:
                published_at = datetime.fromisoformat(raw_ts.replace("Z", "+00:00")).replace(tzinfo=None)
            except (ValueError, AttributeError):
                pass

        signal = ReplaySignal(
            source_type=record.get("source_type"),
            source_name=record.get("source_name"),
            title=record.get("title"),
            published_at=published_at,
            summary=record.get("summary"),
            body=record.get("body"),
            language=record.get("language"),
            url=record.get("url"),
            filter_score=record.get("filter_score"),
            category_hint=record.get("category_hint"),
            matched_keywords=record.get("matched_keywords"),
            status="pending",
            release_order=idx,
            raw_payload=record,
        )
        signals.append(signal)

    db.add_all(signals)
    db.commit()
    return len(signals)


def get_status(db: Session) -> dict:
    rows = (
        db.query(ReplaySignal.status, func.count(ReplaySignal.id))
        .group_by(ReplaySignal.status)
        .all()
    )
    counts = {row[0]: row[1] for row in rows}
    total = sum(counts.values())
    return {
        "total": total,
        "pending": counts.get("pending", 0),
        "released": counts.get("released", 0),
        "processed": counts.get("processed", 0),
        "rejected": counts.get("rejected", 0),
    }


def release_next(db: Session) -> ReplaySignal:
    signal = (
        db.query(ReplaySignal)
        .filter(ReplaySignal.status == "pending")
        .order_by(ReplaySignal.release_order)
        .with_for_update(skip_locked=True)
        .first()
    )
    if not signal:
        raise not_found("No pending signals remain.")

    signal.status = "released"
    signal.released_at = utcnow()
    db.commit()
    db.refresh(signal)
    return signal


def get_signals_by_status(db: Session, status: str) -> list[ReplaySignal]:
    return (
        db.query(ReplaySignal)
        .filter(ReplaySignal.status == status)
        .order_by(ReplaySignal.release_order)
        .all()
    )


def reset_all(db: Session) -> int:
    count = (
        db.query(ReplaySignal)
        .update(
            {"status": "pending", "released_at": None, "processed_at": None},
            synchronize_session=False,
        )
    )
    db.commit()
    return count


def clear_all(db: Session) -> int:
    count = db.query(ReplaySignal).count()
    db.query(ReplaySignal).delete()
    db.commit()
    return count
