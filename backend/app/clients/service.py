from sqlalchemy.orm import Session

from app.clients.models import Client, ClientAsset

# ---------------------------------------------------------------------------
# Seed data — fictional companies and assets for demo purposes
# Assets are placed near real crisis-prone areas to produce interesting matches
# ---------------------------------------------------------------------------

_CLIENTS = [
    {"name": "Northline Logistics",     "industry": "Logistics",     "description": "North American freight and distribution network."},
    {"name": "HarbourGrid Energy",      "industry": "Energy",        "description": "Energy infrastructure across North America."},
    {"name": "Aster Retail Group",      "industry": "Retail",        "description": "Consumer retail chain with regional hubs."},
    {"name": "Pacific Health Response", "industry": "Healthcare",    "description": "Global health supply and emergency response."},
    {"name": "Summit Manufacturing",    "industry": "Manufacturing", "description": "Heavy manufacturing with western North American facilities."},
]

_ASSETS = [
    # Northline Logistics
    {"client": "Northline Logistics", "name": "Idaho Field Site",             "asset_type": "field_site",          "latitude": 43.00,  "longitude": -113.50, "city": "Blaine County",   "region": "Idaho",          "country": "USA",    "criticality": "high"},
    {"client": "Northline Logistics", "name": "Vancouver Distribution Center","asset_type": "distribution_center", "latitude": 49.28,  "longitude": -123.12, "city": "Vancouver",       "region": "British Columbia","country": "Canada", "criticality": "high"},
    {"client": "Northline Logistics", "name": "Calgary Warehouse",            "asset_type": "warehouse",           "latitude": 51.04,  "longitude": -114.07, "city": "Calgary",         "region": "Alberta",        "country": "Canada", "criticality": "medium"},
    {"client": "Northline Logistics", "name": "Seattle Port Office",          "asset_type": "port_facility",       "latitude": 47.61,  "longitude": -122.33, "city": "Seattle",         "region": "Washington",     "country": "USA",    "criticality": "critical"},
    # HarbourGrid Energy
    {"client": "HarbourGrid Energy",  "name": "Houston Operations Hub",       "asset_type": "office",              "latitude": 29.76,  "longitude": -95.37,  "city": "Houston",         "region": "Texas",          "country": "USA",    "criticality": "high"},
    {"client": "HarbourGrid Energy",  "name": "San Francisco Supplier Hub",   "asset_type": "office",              "latitude": 37.77,  "longitude": -122.42, "city": "San Francisco",   "region": "California",     "country": "USA",    "criticality": "medium"},
    {"client": "HarbourGrid Energy",  "name": "Edmonton Facility",            "asset_type": "manufacturing_site",  "latitude": 53.55,  "longitude": -113.49, "city": "Edmonton",        "region": "Alberta",        "country": "Canada", "criticality": "critical"},
    # Aster Retail Group
    {"client": "Aster Retail Group",  "name": "Los Angeles Retail Hub",       "asset_type": "retail_hub",          "latitude": 34.05,  "longitude": -118.24, "city": "Los Angeles",     "region": "California",     "country": "USA",    "criticality": "high"},
    {"client": "Aster Retail Group",  "name": "New York Support Center",      "asset_type": "office",              "latitude": 40.71,  "longitude": -74.01,  "city": "New York",        "region": "New York",       "country": "USA",    "criticality": "medium"},
    {"client": "Aster Retail Group",  "name": "Toronto Data Office",          "asset_type": "office",              "latitude": 43.65,  "longitude": -79.38,  "city": "Toronto",         "region": "Ontario",        "country": "Canada", "criticality": "low"},
    # Pacific Health Response
    {"client": "Pacific Health Response","name": "Jerusalem Regional Office", "asset_type": "office",              "latitude": 31.77,  "longitude":  35.21,  "city": "Jerusalem",       "region": "Jerusalem",      "country": "Israel", "criticality": "critical"},
    {"client": "Pacific Health Response","name": "Vancouver Health Hub",      "asset_type": "health_supply_hub",   "latitude": 49.25,  "longitude": -123.10, "city": "Vancouver",       "region": "British Columbia","country": "Canada", "criticality": "high"},
    {"client": "Pacific Health Response","name": "London Coordination Office","asset_type": "office",              "latitude": 51.51,  "longitude":  -0.13,  "city": "London",          "region": "England",        "country": "UK",     "criticality": "medium"},
    # Summit Manufacturing
    {"client": "Summit Manufacturing","name": "Boise Production Site",        "asset_type": "manufacturing_site",  "latitude": 43.61,  "longitude": -116.20, "city": "Boise",           "region": "Idaho",          "country": "USA",    "criticality": "high"},
    {"client": "Summit Manufacturing","name": "Phoenix Field Station",         "asset_type": "field_site",          "latitude": 33.45,  "longitude": -112.07, "city": "Phoenix",         "region": "Arizona",        "country": "USA",    "criticality": "medium"},
    {"client": "Summit Manufacturing","name": "Calgary Manufacturing Site",    "asset_type": "manufacturing_site",  "latitude": 51.05,  "longitude": -114.07, "city": "Calgary",         "region": "Alberta",        "country": "Canada", "criticality": "critical"},

    # --- International assets placed to match the early Wikinews demo articles ---
    # Coordinates set at city centres so security/bombing events (small radius) still match.
    {"client": "Pacific Health Response","name": "Jakarta Health Office",     "asset_type": "health_supply_hub",   "latitude": -6.2000, "longitude": 106.8456, "city": "Jakarta",     "region": "Jakarta",        "country": "Indonesia",   "criticality": "high"},     # art 1: Indonesia tsunami
    {"client": "Pacific Health Response","name": "Islamabad Field Office",     "asset_type": "office",              "latitude": 33.6844, "longitude":  73.0479, "city": "Islamabad",   "region": "Islamabad",      "country": "Pakistan",    "criticality": "high"},     # art 4: Bhutto (Rawalpindi)
    {"client": "Pacific Health Response","name": "Kabul Aid Station",          "asset_type": "field_site",          "latitude": 34.5553, "longitude":  69.2075, "city": "Kabul",       "region": "Kabul",          "country": "Afghanistan", "criticality": "critical"}, # art 9,22: Kabul bombings
    {"client": "Pacific Health Response","name": "Mumbai Health Hub",          "asset_type": "health_supply_hub",   "latitude": 19.0760, "longitude":  72.8777, "city": "Mumbai",      "region": "Maharashtra",    "country": "India",       "criticality": "high"},     # art 18: Mumbai blasts
    {"client": "Northline Logistics", "name": "Moscow Logistics Office",       "asset_type": "office",              "latitude": 55.7558, "longitude":  37.6173, "city": "Moscow",      "region": "Moscow",         "country": "Russia",      "criticality": "medium"},   # art 5: Moscow train bombing
    {"client": "Northline Logistics", "name": "Minsk Depot",                   "asset_type": "distribution_center", "latitude": 53.9006, "longitude":  27.5590, "city": "Minsk",       "region": "Minsk",          "country": "Belarus",     "criticality": "medium"},   # art 2: Belarus subway bombing
    {"client": "Aster Retail Group",  "name": "Fukuoka Retail Office",        "asset_type": "retail_hub",          "latitude": 33.5904, "longitude": 130.4017, "city": "Fukuoka",     "region": "Kyushu",         "country": "Japan",       "criticality": "medium"},   # art 7: southern Japan earthquake (300km radius)
    {"client": "HarbourGrid Energy",  "name": "Karachi Energy Office",        "asset_type": "office",              "latitude": 24.8607, "longitude":  67.0011, "city": "Karachi",     "region": "Sindh",          "country": "Pakistan",    "criticality": "high"},     # art 6: Karachi base attack
]


def seed_clients_and_assets(db: Session) -> tuple[int, int]:
    """Wipe and re-seed all demo clients and assets. Safe to call multiple times."""
    db.query(ClientAsset).delete()
    db.query(Client).delete()
    db.commit()

    client_map: dict[str, int] = {}
    for c in _CLIENTS:
        obj = Client(name=c["name"], industry=c["industry"], description=c["description"])
        db.add(obj)
        db.flush()
        client_map[c["name"]] = obj.id

    assets_added = 0
    for a in _ASSETS:
        client_id = client_map[a["client"]]
        db.add(ClientAsset(
            client_id=client_id,
            name=a["name"],
            asset_type=a["asset_type"],
            latitude=a["latitude"],
            longitude=a["longitude"],
            city=a["city"],
            region=a["region"],
            country=a["country"],
            criticality=a["criticality"],
        ))
        assets_added += 1

    db.commit()
    return len(_CLIENTS), assets_added


def get_clients(db: Session) -> list[Client]:
    return db.query(Client).order_by(Client.name).all()


def get_client_assets(db: Session, client_id: int) -> list[ClientAsset]:
    return db.query(ClientAsset).filter(ClientAsset.client_id == client_id).all()


def get_all_assets(db: Session) -> list[ClientAsset]:
    return db.query(ClientAsset).order_by(ClientAsset.client_id).all()
