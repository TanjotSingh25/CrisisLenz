import httpx

EONET_BASE = "https://eonet.gsfc.nasa.gov/api/v3"


def fetch_events(days: int = 90, status: str = "open", limit: int = 50) -> dict:
    url = f"{EONET_BASE}/events"
    params = {"days": days, "status": status, "limit": limit}
    with httpx.Client(timeout=30) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()
