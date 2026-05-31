"""create replay_signals table

Revision ID: 0001
Revises:
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "replay_signals",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("source_type", sa.String(100), nullable=True),
        sa.Column("source_name", sa.String(200), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("published_at", sa.DateTime(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("language", sa.String(10), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("filter_score", sa.Float(), nullable=True),
        sa.Column("category_hint", sa.String(100), nullable=True),
        sa.Column("matched_keywords", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("release_order", sa.Integer(), nullable=True),
        sa.Column("released_at", sa.DateTime(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_replay_signals_status", "replay_signals", ["status"])
    op.create_index("ix_replay_signals_release_order", "replay_signals", ["release_order"])


def downgrade() -> None:
    op.drop_index("ix_replay_signals_release_order", table_name="replay_signals")
    op.drop_index("ix_replay_signals_status", table_name="replay_signals")
    op.drop_table("replay_signals")
