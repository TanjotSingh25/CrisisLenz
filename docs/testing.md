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
Expected — all Wikinews signals already pending:
```json
{
  "total": 897,
  "pending": 897,
  "released": 0,
  "processed": 0,
  "rejected": 0,
  "by_source_type": {
    "wikinews_dump": { "pending": 847, "released": 0, "processed": 0, "rejected": 0 },
    "eonet_event":   { "pending": 50,  "released": 0, "processed": 0, "rejected": 0 }
  }
}
```

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
{ "message": "Reset 897 signals to pending (all sources)." }
```

### Reset only one source type
```bash
curl -X POST "http://localhost:8000/replay/reset?source_type=wikinews_dump"
```
Expected:
```json
{ "message": "Reset 847 signals to pending (source_type='wikinews_dump')." }
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

**Requires `GEMINI_API_KEY` in your `.env` file.**

### Setup
```bash
# In your .env file:
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-2.5-flash   # or leave default
```
Restart if you just added the key:
```bash
docker compose restart backend
```

### Analyze a specific released signal
```bash
# Step 1: release a signal, note the id
curl -X POST http://localhost:8000/replay/next

# Step 2: analyze it (replace 1 with actual id)
curl -X POST http://localhost:8000/ai/analyze-signal/1
```
Expected if accepted (operationally relevant):
```json
{
  "signal_id": 1,
  "outcome": "accepted",
  "analysis_id": 1,
  "event_id": 1,
  "is_event_worthy": true,
  "event_type": "bombing",
  "severity": "high",
  "confidence": 0.92,
  "title": "Bomb attack on Jerusalem bus"
}
```
Expected if rejected (noise/irrelevant):
```json
{
  "signal_id": 1,
  "outcome": "rejected",
  "analysis_id": 1,
  "is_event_worthy": false,
  "rejection_reason": "Routine political interview with no immediate operational risk."
}
```

### Analyze next released signal in queue
```bash
# Release a few first
curl -X POST http://localhost:8000/replay/next
curl -X POST http://localhost:8000/replay/next

# Analyze the oldest unanalyzed released signal
curl -X POST http://localhost:8000/ai/analyze-next-released
```

### Analyze an EONET event (coordinates should be preserved)
```bash
curl -X POST "http://localhost:8000/replay/next?source_type=eonet_event"
# Note the id, then:
curl -X POST http://localhost:8000/ai/analyze-signal/<id>
```
Expected: `latitude` and `longitude` match the original EONET signal values.

### View all created events
```bash
curl http://localhost:8000/events
```
Returns list of accepted events, newest first.

### View a specific event
```bash
curl http://localhost:8000/events/1
```

### View full AI analysis output (including reasoning)
```bash
curl http://localhost:8000/ai/analysis/1
```
Returns the full Gemini response including `reasoning_brief`, `business_impact`, `recommended_action`.

### Confirm signal statuses updated
```bash
curl http://localhost:8000/replay/status
```
`processed` count increments for accepted signals, `rejected` count for noise.

### Error cases
```bash
# Signal not yet released → 422
curl -X POST http://localhost:8000/ai/analyze-signal/999

# Signal already analyzed → 409
curl -X POST http://localhost:8000/ai/analyze-signal/1  # second time
```

### Interactive API docs
All endpoints available at: `http://localhost:8000/docs`

---

## Redesign — Decoupled Ingest Pipeline

The `POST /signals/ingest` endpoint is now the primary entry point. It accepts any signal JSON directly — no simulator DB lookup needed. The simulator feeds this endpoint for the demo; in production a live API connector would call it instead.

### POST /signals/ingest — direct signal submission (production-style path)
```bash
# Feed any signal JSON directly to the pipeline
curl -X POST http://localhost:8000/signals/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "source_type": "wikinews_dump",
    "source_name": "Wikinews",
    "title": "Bomb on Jerusalem bus kills one, over 30 injured",
    "summary": "A bomb explosion wounded over 30 people at a crowded bus stop in Jerusalem.",
    "body": "Full article text here...",
    "category_hint": "political_security",
    "matched_keywords": ["attack", "bomb", "injured"]
  }'
```
Expected: same `AnalysisResponse` as analyze-signal. No simulator record needed.

### POST /replay/release-and-analyze — one-button demo flow
```bash
# Releases next pending signal AND immediately analyzes it — single call
curl -X POST http://localhost:8000/replay/release-and-analyze

# Release and analyze an EONET event specifically
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"
```
Expected: full analysis outcome in one response. This is the primary demo endpoint.

### Full demo sequence (clean run)
```bash
# 1. Check everything is pending
curl http://localhost:8000/replay/status

# 2. One call: release + analyze a Wikinews article
curl -X POST http://localhost:8000/replay/release-and-analyze

# 3. One call: release + analyze an EONET event
curl -X POST "http://localhost:8000/replay/release-and-analyze?source_type=eonet_event"

# 4. See the events that were created
curl http://localhost:8000/events

# 5. Reset everything and repeat
curl -X POST http://localhost:8000/replay/reset
```

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
{ "clients_seeded": 5, "assets_seeded": 16 }
```

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
