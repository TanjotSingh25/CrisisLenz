"""make replay_signal_id nullable in ai_analyses and events

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-02

Allows signals that arrive via POST /signals/ingest (not through the
replay simulator) to be analyzed and stored without a replay_signal FK.
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("ai_analyses", "replay_signal_id", nullable=True)
    op.alter_column("events", "replay_signal_id", nullable=True)


def downgrade() -> None:
    op.alter_column("events", "replay_signal_id", nullable=False)
    op.alter_column("ai_analyses", "replay_signal_id", nullable=False)
