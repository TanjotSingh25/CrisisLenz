"""add clients, client_assets, event_asset_impacts tables and seed demo data

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-02
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ---------------------------------------------------------------------------
# Seed data (mirrors app/clients/service.py _CLIENTS / _ASSETS)
# ---------------------------------------------------------------------------
_CLIENTS = [
    {"name": "Northline Logistics",     "industry": "Logistics",     "description": "North American freight and distribution network."},
    {"name": "HarbourGrid Energy",      "industry": "Energy",        "description": "Energy infrastructure across North America."},
    {"name": "Aster Retail Group",      "industry": "Retail",        "description": "Consumer retail chain with regional hubs."},
    {"name": "Pacific Health Response", "industry": "Healthcare",    "description": "Global health supply and emergency response."},
    {"name": "Summit Manufacturing",    "industry": "Manufacturing", "description": "Heavy manufacturing with western North American facilities."},
]

_ASSETS = [
    # Northline Logistics (id 1)
    {"client": "Northline Logistics", "name": "Idaho Field Site",              "asset_type": "field_site",          "latitude": 43.00,  "longitude": -113.50, "city": "Blaine County",    "region": "Idaho",           "country": "USA",    "criticality": "high"},
    {"client": "Northline Logistics", "name": "Vancouver Distribution Center", "asset_type": "distribution_center", "latitude": 49.28,  "longitude": -123.12, "city": "Vancouver",        "region": "British Columbia","country": "Canada", "criticality": "high"},
    {"client": "Northline Logistics", "name": "Calgary Warehouse",             "asset_type": "warehouse",           "latitude": 51.04,  "longitude": -114.07, "city": "Calgary",          "region": "Alberta",         "country": "Canada", "criticality": "medium"},
    {"client": "Northline Logistics", "name": "Seattle Port Office",           "asset_type": "port_facility",       "latitude": 47.61,  "longitude": -122.33, "city": "Seattle",          "region": "Washington",      "country": "USA",    "criticality": "critical"},
    # HarbourGrid Energy (id 2)
    {"client": "HarbourGrid Energy",  "name": "Houston Operations Hub",        "asset_type": "office",              "latitude": 29.76,  "longitude":  -95.37, "city": "Houston",          "region": "Texas",           "country": "USA",    "criticality": "high"},
    {"client": "HarbourGrid Energy",  "name": "San Francisco Supplier Hub",    "asset_type": "office",              "latitude": 37.77,  "longitude": -122.42, "city": "San Francisco",    "region": "California",      "country": "USA",    "criticality": "medium"},
    {"client": "HarbourGrid Energy",  "name": "Edmonton Facility",             "asset_type": "manufacturing_site",  "latitude": 53.55,  "longitude": -113.49, "city": "Edmonton",         "region": "Alberta",         "country": "Canada", "criticality": "critical"},
    # Aster Retail Group (id 3)
    {"client": "Aster Retail Group",  "name": "Los Angeles Retail Hub",        "asset_type": "retail_hub",          "latitude": 34.05,  "longitude": -118.24, "city": "Los Angeles",      "region": "California",      "country": "USA",    "criticality": "high"},
    {"client": "Aster Retail Group",  "name": "New York Support Center",       "asset_type": "office",              "latitude": 40.71,  "longitude":  -74.01, "city": "New York",         "region": "New York",        "country": "USA",    "criticality": "medium"},
    {"client": "Aster Retail Group",  "name": "Toronto Data Office",           "asset_type": "office",              "latitude": 43.65,  "longitude":  -79.38, "city": "Toronto",          "region": "Ontario",         "country": "Canada", "criticality": "low"},
    # Pacific Health Response (id 4)
    {"client": "Pacific Health Response","name": "Jerusalem Regional Office",  "asset_type": "office",              "latitude": 31.77,  "longitude":   35.21, "city": "Jerusalem",        "region": "Jerusalem",       "country": "Israel", "criticality": "critical"},
    {"client": "Pacific Health Response","name": "Vancouver Health Hub",       "asset_type": "health_supply_hub",   "latitude": 49.25,  "longitude": -123.10, "city": "Vancouver",        "region": "British Columbia","country": "Canada", "criticality": "high"},
    {"client": "Pacific Health Response","name": "London Coordination Office", "asset_type": "office",              "latitude": 51.51,  "longitude":   -0.13, "city": "London",           "region": "England",         "country": "UK",     "criticality": "medium"},
    # Summit Manufacturing (id 5)
    {"client": "Summit Manufacturing","name": "Boise Production Site",         "asset_type": "manufacturing_site",  "latitude": 43.61,  "longitude": -116.20, "city": "Boise",            "region": "Idaho",           "country": "USA",    "criticality": "high"},
    {"client": "Summit Manufacturing","name": "Phoenix Field Station",          "asset_type": "field_site",          "latitude": 33.45,  "longitude": -112.07, "city": "Phoenix",          "region": "Arizona",         "country": "USA",    "criticality": "medium"},
    {"client": "Summit Manufacturing","name": "Calgary Manufacturing Site",     "asset_type": "manufacturing_site",  "latitude": 51.05,  "longitude": -114.07, "city": "Calgary",          "region": "Alberta",         "country": "Canada", "criticality": "critical"},
]


def upgrade() -> None:
    # --- clients ---
    op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("industry", sa.String(100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- client_assets ---
    op.create_table(
        "client_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("asset_type", sa.String(50), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=True),
        sa.Column("criticality", sa.String(20), nullable=False, server_default="medium"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_client_assets_client_id", "client_assets", ["client_id"])

    # --- event_asset_impacts ---
    op.create_table(
        "event_asset_impacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("client_asset_id", sa.Integer(), nullable=False),
        sa.Column("distance_km", sa.Float(), nullable=False),
        sa.Column("impact_radius_km", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("match_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["event_id"], ["events.id"]),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["client_asset_id"], ["client_assets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_event_asset_impacts_event_id", "event_asset_impacts", ["event_id"])
    op.create_index("ix_event_asset_impacts_asset_id", "event_asset_impacts", ["client_asset_id"])

    # --- seed demo data ---
    bind = op.get_bind()
    clients_table = sa.table("clients",
        sa.column("id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("industry", sa.String),
        sa.column("description", sa.Text),
    )
    assets_table = sa.table("client_assets",
        sa.column("client_id", sa.Integer),
        sa.column("name", sa.String),
        sa.column("asset_type", sa.String),
        sa.column("latitude", sa.Float),
        sa.column("longitude", sa.Float),
        sa.column("city", sa.String),
        sa.column("region", sa.String),
        sa.column("country", sa.String),
        sa.column("criticality", sa.String),
    )

    for c in _CLIENTS:
        bind.execute(clients_table.insert().values(name=c["name"], industry=c["industry"], description=c["description"]))

    rows = bind.execute(sa.select(clients_table.c.id, clients_table.c.name)).fetchall()
    client_map = {row[1]: row[0] for row in rows}

    for a in _ASSETS:
        bind.execute(assets_table.insert().values(
            client_id=client_map[a["client"]],
            name=a["name"], asset_type=a["asset_type"],
            latitude=a["latitude"], longitude=a["longitude"],
            city=a["city"], region=a["region"], country=a["country"],
            criticality=a["criticality"],
        ))


def downgrade() -> None:
    op.drop_index("ix_event_asset_impacts_asset_id", table_name="event_asset_impacts")
    op.drop_index("ix_event_asset_impacts_event_id", table_name="event_asset_impacts")
    op.drop_table("event_asset_impacts")
    op.drop_index("ix_client_assets_client_id", table_name="client_assets")
    op.drop_table("client_assets")
    op.drop_table("clients")
