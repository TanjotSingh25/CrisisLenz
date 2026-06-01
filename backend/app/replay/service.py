import json
from pathlib import Path

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.common.errors import not_found
from app.common.timestamps import parse_datetime, utcnow
from app.replay.models import ReplaySignal

REPLAY_FILE = Path("/app/data/replay/final_replay_signals.json")


def load_signals(db: Session, reset_existing: bool = True) -> int:
    if reset_existing:
        db.query(ReplaySignal).delete()
        db.commit()

    with open(REPLAY_FILE, "r", encoding="utf-8") as f:
        records = json.load(f)

    signals = [
        ReplaySignal(
            source_type=r.get("source_type"),
            source_name=r.get("source_name"),
            title=r.get("title"),
            published_at=parse_datetime(r.get("published_at")),
            summary=r.get("summary"),
            body=r.get("body"),
            language=r.get("language"),
            url=r.get("url"),
            filter_score=r.get("filter_score"),
            category_hint=r.get("category_hint"),
            matched_keywords=r.get("matched_keywords"),
            status="pending",
            release_order=idx,
            raw_payload=r,
        )
        for idx, r in enumerate(records)
    ]

    db.add_all(signals)
    db.commit()
    return len(signals)


def load_eonet_signals(db: Session, normalized: list[dict], replace_existing: bool = True) -> int:
    if replace_existing:
        db.query(ReplaySignal).filter(ReplaySignal.source_type == "eonet_event").delete()
        db.commit()

    max_order = db.query(func.max(ReplaySignal.release_order)).scalar()
    start = (max_order + 1) if max_order is not None else 0

    signals = [
        ReplaySignal(
            source_type=r.get("source_type", "eonet_event"),
            source_name=r.get("source_name", "NASA EONET"),
            title=r.get("title"),
            published_at=parse_datetime(r.get("published_at")),
            summary=r.get("summary"),
            body=r.get("body"),
            language=r.get("language", "en"),
            url=r.get("url"),
            filter_score=r.get("filter_score"),
            category_hint=r.get("category_hint"),
            matched_keywords=r.get("matched_keywords"),
            latitude=r.get("latitude"),
            longitude=r.get("longitude"),
            event_category=r.get("event_category"),
            event_status=r.get("event_status"),
            status="pending",
            release_order=start + idx,
            raw_payload=r.get("raw_payload", r),
        )
        for idx, r in enumerate(normalized)
    ]

    db.add_all(signals)
    db.commit()
    return len(signals)


def get_status(db: Session) -> dict:
    # Global counts
    global_rows = (
        db.query(ReplaySignal.status, func.count(ReplaySignal.id))
        .group_by(ReplaySignal.status)
        .all()
    )
    counts = {row[0]: row[1] for row in global_rows}

    # Per-source-type counts
    src_rows = (
        db.query(ReplaySignal.source_type, ReplaySignal.status, func.count(ReplaySignal.id))
        .group_by(ReplaySignal.source_type, ReplaySignal.status)
        .all()
    )
    by_source: dict[str, dict[str, int]] = {}
    for src_type, status, count in src_rows:
        key = src_type or "unknown"
        if key not in by_source:
            by_source[key] = {"pending": 0, "released": 0, "processed": 0, "rejected": 0}
        if status in by_source[key]:
            by_source[key][status] = count

    return {
        "total": sum(counts.values()),
        "pending": counts.get("pending", 0),
        "released": counts.get("released", 0),
        "processed": counts.get("processed", 0),
        "rejected": counts.get("rejected", 0),
        "by_source_type": by_source,
    }


def release_next(db: Session, source_type: str | None = None) -> ReplaySignal:
    query = (
        db.query(ReplaySignal)
        .filter(ReplaySignal.status == "pending")
    )
    if source_type:
        query = query.filter(ReplaySignal.source_type == source_type)

    signal = query.order_by(ReplaySignal.release_order).with_for_update(skip_locked=True).first()

    if not signal:
        detail = "No pending signals remain"
        if source_type:
            detail += f" for source_type '{source_type}'"
        raise not_found(detail + ".")

    signal.status = "released"
    signal.released_at = utcnow()
    db.commit()
    db.refresh(signal)
    return signal


def get_signals_by_status(
    db: Session, status: str, source_type: str | None = None
) -> list[ReplaySignal]:
    query = db.query(ReplaySignal).filter(ReplaySignal.status == status)
    if source_type:
        query = query.filter(ReplaySignal.source_type == source_type)
    return query.order_by(ReplaySignal.release_order).all()


def reset_all(db: Session) -> int:
    count = db.query(ReplaySignal).update(
        {"status": "pending", "released_at": None, "processed_at": None},
        synchronize_session=False,
    )
    db.commit()
    return count


def clear_all(db: Session) -> int:
    count = db.query(ReplaySignal).count()
    db.query(ReplaySignal).delete()
    db.commit()
    return count
