"""add unique constraints on (event_id, client_asset_id) for impacts and alerts

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-14

Backs the existing application-level duplicate prevention with DB constraints.
De-dupes any existing rows first (FK-safe order) so the migration cannot fail
on pre-existing data.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Drop duplicate alerts (keep lowest id).
    bind.execute(sa.text(
        "DELETE FROM client_alerts a USING client_alerts b "
        "WHERE a.id > b.id AND a.event_id = b.event_id "
        "AND a.client_asset_id = b.client_asset_id"
    ))
    # 2. Drop alerts that reference impact rows we are about to remove as dups.
    bind.execute(sa.text(
        "DELETE FROM client_alerts WHERE event_asset_impact_id IN ("
        "  SELECT a.id FROM event_asset_impacts a "
        "  JOIN event_asset_impacts b "
        "    ON a.event_id = b.event_id AND a.client_asset_id = b.client_asset_id "
        "  WHERE a.id > b.id)"
    ))
    # 3. Drop duplicate impacts (keep lowest id).
    bind.execute(sa.text(
        "DELETE FROM event_asset_impacts a USING event_asset_impacts b "
        "WHERE a.id > b.id AND a.event_id = b.event_id "
        "AND a.client_asset_id = b.client_asset_id"
    ))

    op.create_unique_constraint(
        "uq_event_asset_impacts_event_asset",
        "event_asset_impacts",
        ["event_id", "client_asset_id"],
    )
    op.create_unique_constraint(
        "uq_client_alerts_event_asset",
        "client_alerts",
        ["event_id", "client_asset_id"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_client_alerts_event_asset", "client_alerts", type_="unique")
    op.drop_constraint("uq_event_asset_impacts_event_asset", "event_asset_impacts", type_="unique")
