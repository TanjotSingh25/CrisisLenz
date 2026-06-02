from functools import lru_cache
from pathlib import Path

import yaml

RULES_FILE = Path("/app/config/impact_rules.yaml")

# Normalise Gemini event_type variants to the keys used in impact_rules.yaml
_ALIASES: dict[str, str] = {
    "forest_fire": "wildfire",
    "explosion": "bombing",
    "explosion_attack": "bombing",
    "bomb": "bombing",
    "riot": "civil_unrest",
    "protest": "civil_unrest",
    "blackout": "power_outage",
    "storm": "severe_storm",
    "hurricane": "severe_storm",
    "cyclone": "severe_storm",
    "tornado": "severe_storm",
    "typhoon": "severe_storm",
    "landslide": "industrial_incident",
    "other": "default",
}


@lru_cache(maxsize=1)
def load_rules() -> dict:
    with open(RULES_FILE, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_impact_radius_km(event_type: str | None, severity: str | None) -> float:
    rules = load_rules()
    normalized = _ALIASES.get(event_type or "", event_type or "")
    type_rules = rules.get(normalized) or rules.get("default", {})
    return float(type_rules.get(severity or "unknown") or type_rules.get("unknown", 50))
