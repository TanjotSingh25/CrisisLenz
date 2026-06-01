"""add geo and event columns to replay_signals

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-31

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("replay_signals", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("replay_signals", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("replay_signals", sa.Column("event_category", sa.String(100), nullable=True))
    op.add_column("replay_signals", sa.Column("event_status", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("replay_signals", "event_status")
    op.drop_column("replay_signals", "event_category")
    op.drop_column("replay_signals", "longitude")
    op.drop_column("replay_signals", "latitude")
