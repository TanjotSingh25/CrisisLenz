"""add client_alerts table

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-05
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "client_alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("client_asset_id", sa.Integer(), nullable=False),
        sa.Column("event_asset_impact_id", sa.Integer(), nullable=False),
        sa.Column("alert_title", sa.Text(), nullable=True),
        sa.Column("alert_summary", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="new"),
        sa.Column("delivery_channel", sa.String(50), nullable=False, server_default="simulated_dashboard"),
        sa.Column("delivery_status", sa.String(20), nullable=False, server_default="not_sent"),
        sa.Column("distance_km", sa.Float(), nullable=True),
        sa.Column("impact_radius_km", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("dismissed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["client_asset_id"], ["client_assets.id"]),
        sa.ForeignKeyConstraint(["event_asset_impact_id"], ["event_asset_impacts.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_alerts_event_id", "client_alerts", ["event_id"])
    op.create_index("ix_client_alerts_client_id", "client_alerts", ["client_id"])
    op.create_index("ix_client_alerts_client_asset_id", "client_alerts", ["client_asset_id"])
    op.create_index("ix_client_alerts_status", "client_alerts", ["status"])
    op.create_index("ix_client_alerts_risk_level", "client_alerts", ["risk_level"])


def downgrade() -> None:
    op.drop_index("ix_client_alerts_risk_level", table_name="client_alerts")
    op.drop_index("ix_client_alerts_status", table_name="client_alerts")
    op.drop_index("ix_client_alerts_client_asset_id", table_name="client_alerts")
    op.drop_index("ix_client_alerts_client_id", table_name="client_alerts")
    op.drop_index("ix_client_alerts_event_id", table_name="client_alerts")
    op.drop_table("client_alerts")
