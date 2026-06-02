from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.clients import service
from app.clients.schemas import ClientAssetOut, ClientOut, SeedResponse
from app.database import get_db

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("/seed", response_model=SeedResponse)
def seed_clients(db: Session = Depends(get_db)):
    """Wipe and re-seed all demo clients and assets."""
    clients, assets = service.seed_clients_and_assets(db)
    return SeedResponse(clients_seeded=clients, assets_seeded=assets)


@router.get("", response_model=list[ClientOut])
def list_clients(db: Session = Depends(get_db)):
    return service.get_clients(db)


@router.get("/{client_id}/assets", response_model=list[ClientAssetOut])
def list_client_assets(client_id: int, db: Session = Depends(get_db)):
    return service.get_client_assets(db, client_id)


@router.get("/assets/all", response_model=list[ClientAssetOut])
def list_all_assets(db: Session = Depends(get_db)):
    return service.get_all_assets(db)
