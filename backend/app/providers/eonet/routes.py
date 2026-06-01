import httpx
from fastapi import APIRouter, HTTPException

from app.providers.eonet import client, snapshot_service

router = APIRouter(prefix="/eonet", tags=["eonet"])


@router.post("/fetch-snapshot")
def fetch_snapshot(days: int = 90, status: str = "open", limit: int = 50):
    """Fetch events from the live NASA EONET API and save as a local snapshot file."""
    try:
        data = client.fetch_events(days=days, status=status, limit=limit)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"EONET API returned {e.response.status_code}")
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Could not reach EONET API: {e}")

    path = snapshot_service.save_snapshot(data)
    return {
        "filename": path.name,
        "events_fetched": len(data.get("events", [])),
        "message": f"Snapshot saved. Load it into the simulator via POST /replay/load-eonet.",
    }


@router.get("/snapshots")
def list_snapshots():
    """List all locally saved EONET snapshot files."""
    files = snapshot_service.list_snapshots()
    return {"snapshots": files, "count": len(files)}
