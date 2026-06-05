# Crisis Lens — Testing Guide

Each module's test sequence is below. Run them in order within a module.

---

## Prerequisites

Docker Desktop running. App started with:

```bash
cp .env.example .env   # first time only — fill in GEMINI_API_KEY
docker compose up --build
```

Wait for:
```
Application startup complete.
```

---

## Module 1 — Replay Feed Simulator

Wikinews data is seeded automatically on first startup via Alembic migration 0003.

### Health check
```bash
curl http://localhost:8000/health
```
Expected:
```json
{ "status": "ok" }
```

### Confirm Wikinews data is pre-loaded (no manual load needed)
```bash
curl http://localhost:8000/replay/status
```
Expected — all signals already pending (100 Wikinews + 50 EONET = 150):
```json
{
  "total": 150,
  "pending": 150,
  "released": 0,
  "processed": 0,
  "rejected": 0,
  "by_source_type": {
    "wikinews_dump": { "pending": 100, "released": 0, "processed": 0, "rejected": 0 },
    "eonet_event":   { "pending": 50,  "released": 0, "processed": 0, "rejected": 0 }
  }
}
```
If you see more than 150 (e.g. 200), you have leftover duplicates from earlier seeding. Run `POST /replay/reseed` (after `docker compose restart backend`) to purge and reload a clean 150.

### Release signals one at a time
```bash
# Release next signal (any source type)
curl -X POST http://localhost:8000/replay/next

# Release next Wikinews signal specifically
curl -X POST "http://localhost:8000/replay/next?source_type=wikinews_dump"

# Release next EONET event specifically
curl -X POST "http://localhost:8000/replay/next?source_type=eonet_event"
```
Expected: full signal JSON with `"status": "released"` and `release_order` field.

### View released signals
```bash
curl http://localhost:8000/replay/signals/released

# Filter by source type
curl "http://localhost:8000/replay/signals/released?source_type=eonet_event"
```

### View pending signals
```bash
curl http://localhost:8000/replay/signals/pending
```

### Reset pointer (all signals back to pending, release_order unchanged)
```bash
curl -X POST http://localhost:8000/replay/reset
```
Expected:
```json
{ "message": "Reset 150 signals to pending (all sources)." }
```

### Reset only one source type
```bash
curl -X POST "http://localhost:8000/replay/reset?source_type=wikinews_dump"
```
Expected:
```json
{ "message": "Reset 100 signals to pending (source_type='wikinews_dump')." }
```

### Auto-cycling (no 404 when exhausted)
After all signals are released, calling `/replay/next` again resets and cycles from the beginning automatically.

---

## Module 2 — EONET Snapshot Provider

EONET data is also pre-seeded via migration 0003 (50 events, already in the DB). These endpoints are for future live fetching.

### List saved snapshots
```bash
curl http://localhost:8000/eonet/snapshots
```
Expected:
```json
{ "snapshots": ["eonet_seed_raw.json", "..."], "count": 1 }
```

### Fetch a fresh live snapshot from NASA EONET (optional — needs internet)
```bash
curl -X POST "http://localhost:8000/eonet/fetch-snapshot?days=90&status=open&limit=50"
```
Expected:
```json
{
  "filename": "eonet_events_20260602_120000.json",
  "events_fetched": 47,
  "message": "Snapshot saved. Load it into the simulator via POST /replay/load-eonet."
}
```
File appears in `data/eonet_snapshots/` on your machine.

### Confirm EONET signals in status
```bash
curl http://localhost:8000/replay/status
```
`by_source_type.eonet_event` should show 50 pending.

### Release and inspect an EONET signal
```bash
curl -X POST "http://localhost:8000/replay/next?source_type=eonet_event"
```
Expected: signal with `latitude`, `longitude`, `event_category`, `event_status` populated.

---

## Module 3 — Gemini Live Signal Analysis

**Requires `GEMINI_API_KEY` in your `.env` file and `docker compose restart backend` after adding it.**

### Primary path — submit any signal JSON directly
```bash
curl -X POST http://localhost:8000/signals/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "wikinews_dump",
    "source_name": "Wikinews",
    "title": "Bomb on Jerusalem bus kills one, over 30 injured",
    "summary": "A bomb explosion wounded over 30 people at a crowded bus stop in Jerusalem.",
    "body": "Full article body here...",
    "category_hint": "political_security",
    "matched_keywords": ["attack", "bomb", "injured"]
  }'
```
Only `title` is required. Expected if accepted:
```json
{
  "outcome": "accepted",
  "analysis_id": 1,
  "event_id": 1,
  "is_event_worthy": true,
  "event_type": "bombing",
  "severity": "high",
  "confidence": 0.92,
  "title": "Bomb attack on Jerusalem bus",
  "summary": "A bomb detonated at a Jerusalem bus stop, killing one and injuring over 30.",
  "location_name": "Jerusalem, Israel",
  "latitude": 31.77,
  "longitude": 35.21,
  "business_impact": "Travel disruption and security risk for operations in the Jerusalem area.",
  "recommended_action": "Monitor local security advisories, check staff in the area, review travel policies.",
  "reasoning_brief": "Active bombing event with confirmed casualties at a named location."
}
```
Expected if rejected (noise article):
```json
{
  "outcome": "rejected",
  "analysis_id": 2,
  "is_event_worthy": false,
  "event_type": "other",
  "severity": "low",
  "rejection_reason": "Routine political interview with no immediate operational risk.",
  "reasoning_brief": "Article is informational commentary, no active disruptive event."
}
```

### Demo path — release and analyze in one call
```bash
# Release next Wikinews signal and analyze it immediately
curl -X POST http://localhost:8000/replay/release-and-analyze

# Release and analyze an EONET natural event
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"
```
Returns the same full `AnalysisResponse`. EONET events will have `latitude`/`longitude` already populated — Gemini preserves them.

### View all created events
```bash
curl http://localhost:8000/events
```

### View the full Gemini analysis record for any result
```bash
curl http://localhost:8000/ai/analysis/1
```
Returns everything including `raw_response_json` (the exact JSON Gemini returned).

### Confirm signal statuses
```bash
curl http://localhost:8000/replay/status
```
`processed` increments for accepted signals, `rejected` for noise.

---

## Useful: Reset Everything for a Clean Demo Run
```bash
curl -X POST http://localhost:8000/replay/reset
```
All signals back to pending. Events, analyses, and impact matches remain in the DB.

---

## Module 4 — Client Assets + Impact Matching

Clients and assets are seeded automatically via migration 0006 on first startup.

### Seed (or re-seed) clients and assets
```bash
curl -X POST http://localhost:8000/clients/seed
```
Expected:
```json
{ "clients_seeded": 5, "assets_seeded": 24 }
```

### Curated demo sequence — covers all cases

The first Wikinews articles and EONET wildfires have assets placed to match them. After `POST /clients/seed`, run signals in order from a fresh reset:

```bash
curl -X POST http://localhost:8000/replay/reset
curl -X POST http://localhost:8000/clients/seed

# Article 0 — Jerusalem bombing → ACCEPTED + matches Jerusalem Regional Office
curl -X POST http://localhost:8000/replay/release-and-analyze
curl -X POST http://localhost:8000/impact/match-event/1

# Releasing more Wikinews articles will hit Minsk, Moscow, Karachi, Kabul, etc.
# Article 3 (BBC poll) → REJECTED by Gemini (non-operational commentary)
# An EONET Idaho wildfire → ACCEPTED + matches Idaho Field Site + Boise

# Bulk match everything created so far:
curl -X POST http://localhost:8000/impact/match-unmatched-events
```

Cases the demo covers:
- **Accepted + matched** — Jerusalem bombing, Idaho wildfire
- **Accepted + no nearby asset** — events in regions with no asset
- **Rejected** — BBC poll commentary (article 3)
- **Skipped (no coordinates)** — articles where Gemini couldn't infer a location

### List all clients
```bash
curl http://localhost:8000/clients
```

### List assets for a specific client
```bash
curl http://localhost:8000/clients/1/assets
```

### List all assets
```bash
curl http://localhost:8000/clients/assets/all
```

### View the loaded impact radius rules
```bash
curl http://localhost:8000/impact/rules
```
Returns the full YAML as JSON. Edit `backend/config/impact_rules.yaml` and restart to change rules.

### Match a specific event against client assets
```bash
# First create an event (release + analyze a signal)
curl -X POST http://localhost:8000/replay/release-and-analyze
# Note the event_id from the response, then:
curl -X POST http://localhost:8000/impact/match-event/1
```
Expected for an Idaho wildfire event (high severity, 150km radius):
```json
{
  "event_id": 1,
  "event_title": "Dewoff Wildfire, Blaine, Idaho",
  "event_type": "wildfire",
  "severity": "high",
  "impact_radius_km": 150.0,
  "matches_created": 2,
  "total_matches": 2,
  "affected_assets": [
    {
      "client": "Northline Logistics",
      "asset": "Idaho Field Site",
      "city": "Blaine County",
      "country": "USA",
      "distance_km": 38.4,
      "impact_radius_km": 150.0,
      "risk_level": "high",
      "criticality": "high"
    },
    {
      "client": "Summit Manufacturing",
      "asset": "Boise Production Site",
      "city": "Boise",
      "country": "USA",
      "distance_km": 121.5,
      "impact_radius_km": 150.0,
      "risk_level": "high",
      "criticality": "high"
    }
  ]
}
```
Events with no coordinates return `"skipped": true` with a clear reason.

### Match all events that haven't been matched yet
```bash
curl -X POST http://localhost:8000/impact/match-unmatched-events
```
Returns an array of match results. Good for bulk demo setup after creating several events.

### Retrieve existing matches for an event (no re-matching)
```bash
curl http://localhost:8000/impact/event/1
```

### Full demo sequence with impact matching
```bash
# 1. Seed clients (if needed)
curl -X POST http://localhost:8000/clients/seed

# 2. Release and analyze signals
curl -X POST http://localhost:8000/replay/release-and-analyze
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"

# 3. Match all unmatched events in one call
curl -X POST http://localhost:8000/impact/match-unmatched-events

# 4. See events and their matched assets
curl http://localhost:8000/events
curl http://localhost:8000/impact/event/1
```

---

## EONET End-to-End Demo (most reliable matches)

EONET events already carry coordinates, so they always have a location for impact matching — no dependence on Gemini inferring lat/lon. The first few EONET events are Idaho wildfires that match the **Idaho Field Site** and **Boise Production Site** assets. This is the most dependable demo path.

```bash
# 1. Clean slate
curl -X POST http://localhost:8000/replay/reset
curl -X POST http://localhost:8000/clients/seed

# 2. Release + analyze the next EONET event (an Idaho wildfire)
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"
```
Expected — accepted with coordinates preserved from the source:
```json
{
  "outcome": "accepted",
  "event_id": 1,
  "is_event_worthy": true,
  "event_type": "wildfire",
  "severity": "high",
  "latitude": 43.050333,
  "longitude": -113.935667,
  "business_impact": "...",
  "recommended_action": "..."
}
```

```bash
# 3. Match that event against client assets (use the event_id from step 2)
curl -X POST http://localhost:8000/impact/match-event/1
```
Expected — Idaho wildfire matches nearby assets:
```json
{
  "event_id": 1,
  "event_type": "wildfire",
  "severity": "high",
  "impact_radius_km": 150.0,
  "matches_created": 2,
  "total_matches": 2,
  "affected_assets": [
    { "client": "Northline Logistics", "asset": "Idaho Field Site", "distance_km": 41.2, "risk_level": "high" },
    { "client": "Summit Manufacturing", "asset": "Boise Production Site", "distance_km": 118.5, "risk_level": "high" }
  ]
}
```

```bash
# 4. Run several EONET events and bulk-match them
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"
curl -X POST http://localhost:8000/impact/match-unmatched-events

# 5. Review everything
curl http://localhost:8000/events
```

**Note on Wikinews matching:** Wikinews articles have no coordinates in the source. Gemini must infer them from the article text. After the prompt update, Gemini provides approximate city-level coordinates for named locations (e.g. Jerusalem → 31.78, 35.21), so security/bombing articles with a clear city will match. If an event still comes back with `latitude: null`, the article named no identifiable location and impact matching will skip it — that is the expected "skipped (no coordinates)" case.

---

## Module 5 — Simulated Alert Generation

Turns impact matches into client-facing alert records. No real emails/Slack/SMS — alerts are stored in the DB with `delivery_channel = "simulated_dashboard"` and `delivery_status = "not_sent"`. Alert content is built deterministically from the event + client + asset + impact match (no extra Gemini call).

**Prerequisite:** you need an event that has already been impact-matched (Module 4). Alerts are generated from `event_asset_impacts` rows.

### Generate alerts for one event
```bash
# event_id must already have impact matches
curl -X POST http://localhost:8000/alerts/generate-for-event/14
```
Expected:
```json
{
  "event_id": 14,
  "event_title": "Black Ridge Wildfire, Lincoln, Idaho",
  "impacts_found": 1,
  "alerts_created": 1,
  "alerts_skipped": 0,
  "alerts": [
    { "id": 1, "client": "Northline Logistics", "asset": "Idaho Field Site", "risk_level": "high", "status": "new" }
  ]
}
```

### Duplicate prevention
```bash
# Run the same generate call again — nothing new is created
curl -X POST http://localhost:8000/alerts/generate-for-event/14
```
Expected: `"alerts_created": 0, "alerts_skipped": 1`. The unique rule is `event_id + client_asset_id`.

### Generate alerts for every unmatched impact (bulk)
```bash
curl -X POST http://localhost:8000/alerts/generate-pending
```
Scans all impact matches and creates alerts for any that don't have one yet.

### List alerts (with optional filters)
```bash
curl http://localhost:8000/alerts
curl "http://localhost:8000/alerts?status=new"
curl "http://localhost:8000/alerts?client_id=1"
curl "http://localhost:8000/alerts?event_id=14"
curl "http://localhost:8000/alerts?risk_level=high"
```

### Get one full alert
```bash
curl http://localhost:8000/alerts/1
```
Returns the full record including `alert_title`, `alert_summary`, `recommended_action`, `distance_km`, `impact_radius_km`, and lifecycle timestamps.

### Acknowledge an alert (new → acknowledged)
```bash
curl -X POST http://localhost:8000/alerts/1/acknowledge
```
Expected: `"status": "acknowledged"` with `acknowledged_at` set. Acknowledging a **dismissed** alert returns 409.

### Dismiss an alert (→ dismissed)
```bash
curl -X POST http://localhost:8000/alerts/2/dismiss
```
Expected: `"status": "dismissed"` with `dismissed_at` set. The alert is kept, not deleted.

### Summary (for the future dashboard)
```bash
curl http://localhost:8000/alerts/summary
```
Expected:
```json
{
  "total": 2,
  "new": 0,
  "acknowledged": 1,
  "dismissed": 1,
  "by_risk_level": { "high": 2 }
}
```

### Full Module 5 demo sequence
```bash
# 1. Make sure assets are seeded and an event is matched (Modules 4)
curl -X POST http://localhost:8000/clients/seed
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"   # creates an event
curl -X POST http://localhost:8000/impact/match-event/<event_id>                          # creates impacts

# 2. Generate alerts from those impacts
curl -X POST http://localhost:8000/alerts/generate-for-event/<event_id>

# 3. View, acknowledge, dismiss
curl http://localhost:8000/alerts
curl -X POST http://localhost:8000/alerts/<alert_id>/acknowledge
curl -X POST http://localhost:8000/alerts/<alert_id>/dismiss
curl http://localhost:8000/alerts/summary
```
