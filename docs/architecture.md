# Crisis Lens — Architecture & Module Reference

A running description of what each module does, how data flows through it, and what goes in and out.

---

## Project Overview

Crisis Lens simulates an operational risk intelligence pipeline. Public signals (news articles, natural event feeds) enter the system, get analyzed by AI, and are classified as either structured events (worth acting on) or rejected (noise).

```
Public signal source
      ↓
Replay simulator (controlled release)
      ↓
Gemini live analysis
      ↓
Accepted → structured Event record
Rejected → signal marked rejected
      ↓
(future) Client asset matching
      ↓
(future) Alert generation
      ↓
(future) Dashboard
```

**Stack:** Python 3.12 + FastAPI, PostgreSQL 16, SQLAlchemy 2, Alembic, google-genai, Docker Compose.  
**Architecture:** Modular monolith — clear internal modules, no microservices.

---

## Database Tables

| Table | Purpose |
|---|---|
| `replay_signals` | All incoming signals (Wikinews + EONET), lifecycle tracked via `status` |
| `ai_analyses` | Raw + validated Gemini output, one row per analysis call |
| `events` | Accepted structured events, derived from AI analysis |
| `clients` | Fictional demo client organisations |
| `client_assets` | Client locations with lat/lon and criticality |
| `event_asset_impacts` | Impact matches between events and client assets |

**`alembic_version`** tracks which migrations have run.

---

## Module 1 — Replay Feed Simulator

**Files:** `app/replay/`

### What It Does

Manages a pool of pre-loaded signals and releases them one at a time in a deterministic order. Simulates an external signal provider for demo stability.

### Data Flow

```
data/replay/final_replay_signals.json   (847 Wikinews articles, committed to repo)
data/eonet_snapshots/eonet_seed_normalized.json  (50 EONET events, committed)
      ↓  Alembic migration 0003 (runs once on first startup)
replay_signals table  (all rows, status = "pending")
      ↓  POST /replay/next
signal.status → "released"  (pointer advances via release_order)
      ↓  POST /replay/reset
signal.status → "pending" for all  (pointer resets, rows unchanged)
```

### Key Concepts

- **`release_order`** — fixed integer per signal, assigned on seed. Never changes. Determines replay sequence.
- **Pointer** — not a real pointer. Just `WHERE status='pending' ORDER BY release_order LIMIT 1`.
- **Auto-reset** — when all signals are exhausted, the next call to `/replay/next` resets all statuses and cycles from the beginning. No 404.
- **Two source types** — `wikinews_dump` (news articles) and `eonet_event` (natural events). Both live in the same table, filterable via `?source_type=`.

### Signal Status Lifecycle

```
pending → released → processed   (AI accepted it, event created)
                   → rejected    (AI rejected it)
                   → failed      (Gemini/API error)
```

### Input / Output

| Endpoint | Input | Output |
|---|---|---|
| `GET /replay/status` | — | counts by status and source_type |
| `POST /replay/next` | optional `?source_type=` | one released signal JSON |
| `GET /replay/signals/released` | optional `?source_type=` | list of released signals |
| `POST /replay/reset` | optional `?source_type=` | count of reset signals |

### Signal Record Shape (key fields)

```json
{
  "id": 201,
  "source_type": "wikinews_dump",
  "title": "Bomb on Jerusalem bus kills one",
  "summary": "...",
  "body": "...",
  "category_hint": "political_security",
  "matched_keywords": ["attack", "bomb"],
  "status": "released",
  "release_order": 200,
  "released_at": "2026-06-01T12:00:00",
  "latitude": null,
  "longitude": null
}
```

EONET records additionally have `latitude`, `longitude`, `event_category`, `event_status` populated.

---

## Module 2 — EONET Snapshot Provider

**Files:** `app/providers/eonet/`

### What It Does

Provides a bridge to NASA EONET (Earth Observatory Natural Event Tracker). For the demo, a pre-fetched snapshot of 50 open natural events is committed to the repo and seeded via migration. A live-fetch endpoint exists for future use.

### Data Flow

```
NASA EONET API  (https://eonet.gsfc.nasa.gov/api/v3/events)
      ↓  POST /eonet/fetch-snapshot  (optional, for future updates)
data/eonet_snapshots/eonet_events_YYYYMMDD.json  (raw API response)
      ↓  normalizer.py
Normalized record shape compatible with replay_signals
      ↓  migration 0003 (pre-normalized file seeded at startup)
replay_signals  (source_type = "eonet_event")
```

### Normalization

`providers/eonet/normalizer.py` converts the raw EONET event structure into the replay signal shape:

| EONET field | → | Replay signal field |
|---|---|---|
| `title` | → | `title` |
| `categories[0].id` | → | `event_category` |
| `categories[0].title` | → | generates `summary`, `matched_keywords` |
| `geometry[0].date` | → | `published_at` |
| `geometry[0].coordinates[1]` | → | `latitude` |
| `geometry[0].coordinates[0]` | → | `longitude` |
| `closed` | → | `event_status` ("open" or "closed") |
| full event JSON | → | `raw_payload` |

### Input / Output

| Endpoint | Input | Output |
|---|---|---|
| `POST /eonet/fetch-snapshot` | `?days=`, `?status=`, `?limit=` | filename + event count |
| `GET /eonet/snapshots` | — | list of saved snapshot files |

---

## Module 3 — Gemini Live Signal Analysis

**Files:** `app/ai/`, `app/signals/`, `app/events/`, `app/prompts/`

### What It Does

Accepts any signal payload, sends it to Gemini live, validates the structured response, and either creates an `Event` record (operationally relevant) or rejects the signal (noise). Returns the full AI output — including business impact and recommended action — in the immediate response.

The simulator (Module 1) is entirely separate from this pipeline. The simulator is just one source. In production, a live API connector would call the same endpoint.

### Data Flow

```
POST /signals/ingest  (primary — accepts any JSON)
POST /replay/release-and-analyze  (demo — release_next() then ingest_signal())
      ↓
app/signals/processing.py :: ingest_signal(db, signal_data, replay_signal=None)
  — replay_signal is optional; only provided when signal came from the simulator
      ↓
app/ai/analysis_service.py :: analyze_signal(signal_dict)
  — loads app/prompts/signal_analysis_system.md       (system prompt)
  — loads app/prompts/signal_analysis_user_template.md (fills {{placeholders}})
  — truncates body to 6000 chars
      ↓
app/ai/gemini_client.py :: GeminiClient.analyze_signal(system, user)
  — google-genai SDK, model: gemini-2.5-flash (env: GEMINI_MODEL)
  — response_mime_type: "application/json" → forces structured output
      ↓
Gemini API  (live call)
      ↓
SignalAnalysisResult.model_validate_json(raw_text)  ← Pydantic validates
      ↓
back in processing.py:
  ALWAYS  → create_ai_analysis()   INSERT into ai_analyses

  accepted → create_event()        INSERT into events
             signal.status = "processed"   (if from simulator)

  rejected → signal.status = "rejected"   (if from simulator)

  error    → signal.status = "failed", signal.processing_error set
      ↓
AnalysisResponse  (returned immediately, includes all AI output fields)
```

### Simulator / Pipeline Boundary

```
SIMULATOR (demo only)               PIPELINE (the real product)
────────────────────                ──────────────────────────────
replay_signals table                POST /signals/ingest
POST /replay/next                     only title is required
  → returns signal JSON               any source can call it
       │
       │  for demo convenience
       └──► POST /replay/release-and-analyze
              = release_next() + ingest_signal() in one call
```

`replay_signal_id` in `ai_analyses` and `events` is nullable — signals via direct ingest have no simulator record, which is fine.

### Module Boundaries

The AI layer (`app/ai/`) has zero database imports — portable to other projects.

```
┌─────────────────────────────────┐
│  app/ai/  (reusable)            │
│  gemini_client.py               │
│  prompt_loader.py               │
│  analysis_service.py            │
│  schemas.py                     │
│  — no SQLAlchemy imports —      │
└────────────┬────────────────────┘
             │  dict in / SignalAnalysisResult out
┌────────────▼────────────────────┐
│  app/signals/processing.py      │
│  — ORM ↔ dict conversion        │
│  — DB saves (ai_analyses/events)│
│  — signal status updates        │
└─────────────────────────────────┘
```

### Prompt Files (`backend/app/prompts/`)

**`signal_analysis_system.md`** — analyst role and accept/reject criteria. Edit to tune what counts as operationally relevant.

**`signal_analysis_user_template.md`** — per-signal prompt with `{{placeholder}}` fields. Edit to change what Gemini sees.

No code change needed — save the file and restart the container.

### What Gemini Returns (`SignalAnalysisResult`)

```json
{
  "is_event_worthy": true,
  "rejection_reason": null,
  "event_type": "wildfire",
  "severity": "high",
  "confidence": 0.91,
  "title": "Wildfire near Blaine County, Idaho",
  "summary": "Active wildfire with known coordinates and potential regional disruption.",
  "location_name": "Blaine County, Idaho, United States",
  "latitude": 42.67045,
  "longitude": -113.248133,
  "business_impact": "Potential disruption to local travel and nearby facilities.",
  "recommended_action": "Monitor fire spread, check asset exposure, prepare contingency plans.",
  "reasoning_brief": "EONET event with active open status and confirmed location."
}
```

All fields except `is_event_worthy` and `reasoning_brief` are returned in the `AnalysisResponse` directly. The `GET /ai/analysis/{id}` endpoint additionally returns `raw_response_json` (exact Gemini output) and `prompt_version`.

### DB Tables Written by This Module

**`ai_analyses`** — one row per Gemini call. Full output + `raw_response_json` + `model_name` + `prompt_version`.

**`events`** — one row per accepted signal. Status defaults to `active`.

### Input / Output

| Endpoint | Input | Output |
|---|---|---|
| `POST /signals/ingest` | signal JSON body (only `title` required) | `AnalysisResponse` — **primary path** |
| `POST /replay/release-and-analyze` | optional `?source_type=` | `AnalysisResponse` — **demo convenience** |
| `POST /ai/analyze-signal/{id}` | simulator signal id (must be `released`) | `AnalysisResponse` — debug utility |
| `GET /ai/analysis/{id}` | — | full `AiAnalysisOut` with raw Gemini JSON |
| `GET /events` | `?limit=`, `?offset=` | list of `EventOut` |
| `GET /events/{id}` | — | single `EventOut` |

### Error Handling

| Scenario | Behaviour |
|---|---|
| `GEMINI_API_KEY` not set | 503 with clear message |
| Gemini API error / timeout | signal → `failed`, `processing_error` set |
| Malformed JSON from Gemini | Pydantic validation error → signal → `failed` |
| Signal not found | 404 |
| Signal not yet released (debug endpoint) | 422 |
| Signal already analyzed (debug endpoint) | 409 |

---

## Module 4 — Client Assets + Impact Matching

**Files:** `app/clients/`, `app/impact/`, `backend/config/impact_rules.yaml`

### What It Does

Answers the question: *which client assets could be affected by this event?*

Gemini already extracted `event_type`, `severity`, `latitude`, and `longitude` from the signal. This module uses those fields deterministically — no more AI calls — to calculate which fake client assets fall inside the estimated operational impact zone.

### Data Flow

```
POST /impact/match-event/{event_id}
      ↓
impact/service.py :: match_event(db, event_id)
  — loads Event from DB (has lat/lon/event_type/severity from Gemini)
  — if no coordinates → return skipped response, no match
  ↓
impact/rules.py :: get_impact_radius_km(event_type, severity)
  — loads backend/config/impact_rules.yaml
  — normalises event_type aliases (e.g. "forest_fire" → "wildfire")
  — returns radius in km  e.g. wildfire + high → 150km
  ↓
for each ClientAsset in DB:
  impact/haversine.py :: haversine_km(event_lat, event_lon, asset_lat, asset_lon)
  — if distance <= radius AND no existing match for this (event, asset) pair:
      INSERT into event_asset_impacts
  ↓
returns MatchEventResponse with affected_assets sorted by distance
```

### Key Design Decisions

- **Gemini interprets, backend calculates.** The AI determines what the event is and where. The backend determines which assets are exposed. Radius rules are in a YAML file, not in Gemini's output.
- **"Estimated Operational Impact Zone"** — not "affected area". Crisis Lens is not doing real disaster modelling.
- **Duplicate prevention** — the service checks for existing `(event_id, client_asset_id)` pairs before inserting. Calling match-event twice is safe.
- **Events with no coordinates are handled cleanly** — `skipped: true` with a reason.

### Impact Rules Config (`backend/config/impact_rules.yaml`)

```yaml
wildfire:
  high: 150   # km
  critical: 300
```

Edit this file freely — no code change needed. Restart the container to pick up changes. The `GET /impact/rules` endpoint shows the currently loaded rules.

Event type aliases (normalisation):
- `forest_fire` → `wildfire`
- `bomb`, `explosion` → `bombing`
- `riot`, `protest` → `civil_unrest`
- Unknown types → `default` rules

### Demo Seed Data

5 fictional clients, 16 assets across North America, Jerusalem, and London. Assets are deliberately placed near common crisis locations (Idaho wildfire zone, Jerusalem, Pacific Northwest) to produce interesting matches.

### DB Tables

**`clients`** — 5 fictional companies (name, industry, description)

**`client_assets`** — 16 assets (lat/lon, asset_type, criticality, client_id)

**`event_asset_impacts`** — one row per matched (event, asset) pair. Stores distance, radius, risk_level, and match_reason.

### Input / Output

| Endpoint | Input | Output |
|---|---|---|
| `POST /clients/seed` | — | `{ clients_seeded, assets_seeded }` |
| `GET /clients` | — | list of clients |
| `GET /clients/{id}/assets` | — | assets for one client |
| `GET /clients/assets/all` | — | all assets |
| `POST /impact/match-event/{id}` | event must exist | `MatchEventResponse` |
| `POST /impact/match-unmatched-events` | — | list of `MatchEventResponse` |
| `GET /impact/event/{id}` | — | existing matches for event |
| `GET /impact/rules` | — | loaded YAML rules as JSON |

### Migration 0006

Creates `clients`, `client_assets`, `event_asset_impacts` tables and seeds all demo clients/assets. Runs once at first startup.

---

## Configuration Reference

| Variable | Default | Required |
|---|---|---|
| `DATABASE_URL` | — | Yes |
| `POSTGRES_USER` | — | Yes |
| `POSTGRES_PASSWORD` | — | Yes |
| `POSTGRES_DB` | — | Yes |
| `GEMINI_API_KEY` | `""` | Yes for Module 3 |
| `GEMINI_MODEL` | `gemini-2.5-flash` | No |

---

## Migration History

| ID | Description |
|---|---|
| 0001 | Create `replay_signals` table |
| 0002 | Add `latitude`, `longitude`, `event_category`, `event_status` to `replay_signals` |
| 0003 | Seed `replay_signals` with Wikinews + EONET data (data migration, runs once) |
| 0004 | Create `ai_analyses`, `events` tables; add `processing_error` to `replay_signals` |
| 0005 | Make `replay_signal_id` nullable in `ai_analyses` and `events` |
| 0006 | Create `clients`, `client_assets`, `event_asset_impacts` tables + seed demo data |
