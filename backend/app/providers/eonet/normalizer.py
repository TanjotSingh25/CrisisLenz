CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "wildfires": ["wildfire", "fire"],
    "severeStorms": ["storm", "hurricane", "cyclone", "tornado", "typhoon"],
    "volcanoes": ["volcano", "eruption", "volcanic"],
    "seaAndLakeIce": ["sea ice", "ice"],
    "earthquakes": ["earthquake", "seismic", "tremor"],
    "floods": ["flood", "flooding"],
    "landslides": ["landslide", "mudslide", "debris flow"],
    "drought": ["drought"],
    "dustHaze": ["dust", "haze", "sandstorm"],
    "manmade": ["manmade", "industrial", "spill"],
    "snow": ["snow", "blizzard", "avalanche"],
    "tempExtremes": ["heat wave", "cold wave", "extreme temperature"],
    "waterColor": ["algae bloom", "discoloration"],
}


def normalize_event(event: dict) -> dict:
    categories = event.get("categories", [])
    category_id = categories[0].get("id", "unknown") if categories else "unknown"
    category_title = categories[0].get("title", "Unknown") if categories else "Unknown"

    geometry = event.get("geometry", [])
    first_geom = geometry[0] if geometry else {}

    # Extract coordinates — EONET Point geometry: [longitude, latitude]
    coords = first_geom.get("coordinates")
    latitude = longitude = None
    if coords and first_geom.get("type") == "Point":
        longitude, latitude = float(coords[0]), float(coords[1])

    # Best available date: first geometry date, or closed date
    published_at = first_geom.get("date") or event.get("closed")

    event_status = "closed" if event.get("closed") else "open"

    sources = event.get("sources", [])
    url = event.get("link") or (sources[0].get("url") if sources else None)

    title = event.get("title") or "Unknown EONET Event"
    summary = f"{category_title}: {title} ({event_status})"

    body_lines = [
        "NASA EONET natural event.",
        f"Category: {category_title}",
        f"Status: {event_status}",
    ]
    if latitude is not None and longitude is not None:
        body_lines.append(f"Location: {latitude:.4f}°N, {longitude:.4f}°E")
    mag_val = first_geom.get("magnitudeValue")
    if mag_val:
        body_lines.append(f"Magnitude: {mag_val} {first_geom.get('magnitudeUnit', '').strip()}")

    matched_keywords = CATEGORY_KEYWORDS.get(category_id, [category_title.lower()])

    return {
        "source_type": "eonet_event",
        "source_name": "NASA EONET",
        "title": title,
        "published_at": published_at,
        "summary": summary,
        "body": "\n".join(body_lines),
        "language": "en",
        "url": url,
        "filter_score": None,
        "category_hint": "natural_disaster",
        "matched_keywords": matched_keywords,
        "latitude": latitude,
        "longitude": longitude,
        "event_category": category_id,
        "event_status": event_status,
        "raw_payload": event,
    }
