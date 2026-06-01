import json
from datetime import datetime
from pathlib import Path

SNAPSHOT_DIR = Path("/app/data/eonet_snapshots")


def save_snapshot(data: dict, filename: str | None = None) -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"eonet_events_{ts}.json"
    path = SNAPSHOT_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return path


def load_snapshot(filename: str) -> dict:
    path = SNAPSHOT_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Snapshot not found: {filename}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_snapshots() -> list[str]:
    if not SNAPSHOT_DIR.exists():
        return []
    return sorted([f.name for f in SNAPSHOT_DIR.glob("*.json")], reverse=True)


def latest_snapshot() -> str | None:
    files = list_snapshots()
    return files[0] if files else None
