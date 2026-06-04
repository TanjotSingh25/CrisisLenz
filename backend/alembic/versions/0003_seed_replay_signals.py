"""seed replay_signals with Wikinews and EONET data

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-01

One-time data migration. Reads pre-prepared JSON files from the mounted
data/ volume and inserts all records as pending replay signals.
Runs exactly once — Alembic tracks it and never repeats it.
"""
from typing import Sequence, Union
import json
from datetime import datetime
from pathlib import Path

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

WIKINEWS_FILE = Path("/app/data/replay/final_replay_signals.json")
EONET_FILE = Path("/app/data/eonet_snapshots/eonet_seed_normalized.json")

replay_signals = sa.table(
    "replay_signals",
    sa.column("source_type", sa.String),
    sa.column("source_name", sa.String),
    sa.column("title", sa.Text),
    sa.column("published_at", sa.DateTime),
    sa.column("summary", sa.Text),
    sa.column("body", sa.Text),
    sa.column("language", sa.String),
    sa.column("url", sa.Text),
    sa.column("filter_score", sa.Float),
    sa.column("category_hint", sa.String),
    sa.column("matched_keywords", sa.JSON),
    sa.column("status", sa.String),
    sa.column("release_order", sa.Integer),
    sa.column("raw_payload", sa.JSON),
    sa.column("latitude", sa.Float),
    sa.column("longitude", sa.Float),
    sa.column("event_category", sa.String),
    sa.column("event_status", sa.String),
)


def _parse_dt(ts):
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None


def upgrade() -> None:
    bind = op.get_bind()
    existing = bind.execute(sa.text("SELECT COUNT(*) FROM replay_signals")).scalar()
    if existing > 0:
        return  # already seeded — skip to prevent duplicates

    records = []
    order = 0

    # --- Wikinews signals ---
    if WIKINEWS_FILE.exists():
        wikinews = json.loads(WIKINEWS_FILE.read_text(encoding="utf-8"))
        for r in wikinews:
            records.append({
                "source_type": r.get("source_type"),
                "source_name": r.get("source_name"),
                "title": r.get("title"),
                "published_at": _parse_dt(r.get("published_at")),
                "summary": r.get("summary"),
                "body": r.get("body"),
                "language": r.get("language"),
                "url": r.get("url"),
                "filter_score": r.get("filter_score"),
                "category_hint": r.get("category_hint"),
                "matched_keywords": r.get("matched_keywords"),
                "status": "pending",
                "release_order": order,
                "raw_payload": r,
                "latitude": None,
                "longitude": None,
                "event_category": None,
                "event_status": None,
            })
            order += 1

    # --- EONET signals ---
    if EONET_FILE.exists():
        eonet = json.loads(EONET_FILE.read_text(encoding="utf-8"))
        for r in eonet:
            records.append({
                "source_type": r.get("source_type", "eonet_event"),
                "source_name": r.get("source_name", "NASA EONET"),
                "title": r.get("title"),
                "published_at": _parse_dt(r.get("published_at")),
                "summary": r.get("summary"),
                "body": r.get("body"),
                "language": r.get("language", "en"),
                "url": r.get("url"),
                "filter_score": None,
                "category_hint": r.get("category_hint"),
                "matched_keywords": r.get("matched_keywords"),
                "status": "pending",
                "release_order": order,
                "raw_payload": r.get("raw_payload", r),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
                "event_category": r.get("event_category"),
                "event_status": r.get("event_status"),
            })
            order += 1

    if records:
        op.bulk_insert(replay_signals, records)


def downgrade() -> None:
    op.execute("DELETE FROM replay_signals")
