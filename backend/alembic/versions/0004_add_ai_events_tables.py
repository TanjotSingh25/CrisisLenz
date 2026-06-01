"""add ai_analyses and events tables; add processing_error to replay_signals

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- ai_analyses ---
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("replay_signal_id", sa.Integer(), nullable=False),
        sa.Column("model_name", sa.String(100), nullable=True),
        sa.Column("prompt_version", sa.String(50), nullable=True),
        sa.Column("is_event_worthy", sa.Boolean(), nullable=False),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("location_name", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("business_impact", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("reasoning_brief", sa.Text(), nullable=True),
        sa.Column("raw_response_json", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["replay_signal_id"], ["replay_signals.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_analyses_replay_signal_id", "ai_analyses", ["replay_signal_id"])

    # --- events ---
    op.create_table(
        "events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("replay_signal_id", sa.Integer(), nullable=False),
        sa.Column("ai_analysis_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(20), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("location_name", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("business_impact", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["replay_signal_id"], ["replay_signals.id"]),
        sa.ForeignKeyConstraint(["ai_analysis_id"], ["ai_analyses.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_events_replay_signal_id", "events", ["replay_signal_id"])
    op.create_index("ix_events_status", "events", ["status"])

    # --- add processing_error to replay_signals ---
    op.add_column("replay_signals", sa.Column("processing_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("replay_signals", "processing_error")
    op.drop_index("ix_events_status", table_name="events")
    op.drop_index("ix_events_replay_signal_id", table_name="events")
    op.drop_table("events")
    op.drop_index("ix_ai_analyses_replay_signal_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")
