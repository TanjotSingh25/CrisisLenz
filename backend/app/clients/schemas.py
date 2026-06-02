from datetime import datetime

from pydantic import BaseModel


class ClientAssetOut(BaseModel):
    id: int
    client_id: int
    name: str
    asset_type: str | None
    latitude: float
    longitude: float
    city: str | None
    region: str | None
    country: str | None
    criticality: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClientOut(BaseModel):
    id: int
    name: str
    industry: str | None
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SeedResponse(BaseModel):
    clients_seeded: int
    assets_seeded: int
