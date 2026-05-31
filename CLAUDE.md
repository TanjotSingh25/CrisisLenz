# Crisis Lens — Claude Code Context

## What This Project Is

Crisis Lens is a portfolio/demo prototype targeting Samdesk (a crisis-alerting company). It simulates how public signals enter an intelligence system and become actionable client alerts.

Core flow:
```
Replay signal → Ingest → Gemini analysis → Structured event → Client asset matching → Alert → Dashboard
```

This is NOT a Samdesk clone. It demonstrates signal ingestion pipeline design, AI extraction/enrichment, and client-specific operational alerting.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Database | PostgreSQL 16 |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| AI (later) | Gemini API |
| Frontend (later) | React + Vite + TypeScript |
| Map (later) | Leaflet + OpenStreetMap |
| Container | Docker Compose |

Architecture: **modular monolith** — clear internal modules, no microservices.

---

## Project Layout

```
CrisisLenz/
  CLAUDE.md
  docker-compose.yml
  .env / .env.example
  README.md
  data/
    replay/
      final_replay_signals.json    ← prepared Wikinews replay dataset (seed file)
  backend/
    Dockerfile
    requirements.txt
    alembic.ini
    app/
      main.py
      config.py
      database.py
      replay/          ← Module 1 (current)
      common/
    alembic/
      versions/
```

---

## Module Build Order

1. **Replay Feed Simulator** ← current module
2. Raw signal ingestion pipeline
3. Live Gemini signal-to-event analysis
4. Config-file based impact-radius rules (`config/impact_rules.yaml`)
5. Sample clients and client assets
6. Client impact matching (event location + radius)
7. Simulated alert generation
8. GraphQL API for dashboard reads
9. React dashboard
10. Optional: NASA EONET connector, GDELT connector, replay autoplay
11. Deployment, README, demo video

---

## Current Module: Module 1 — Replay Feed Simulator

**Goal**: Load `data/replay/final_replay_signals.json` into PostgreSQL, track signal statuses, release one signal at a time, reset replay state.

**Table**: `replay_signals`

**Signal statuses**: `pending` → `released` → `processed` / `rejected`

**Endpoints**:
- `GET /health`
- `POST /replay/load` — seed from JSON file
- `GET /replay/status` — counts by status
- `POST /replay/next` — release one pending signal
- `GET /replay/signals/released`
- `GET /replay/signals/pending`
- `POST /replay/reset` — back to all pending
- `DELETE /replay/clear` — wipe table

---

## Data Notes

- `data/replay/final_replay_signals.json` is the **only** data file the app reads at runtime.
- Do NOT parse the raw Wikinews XML dump at runtime. It is an offline prep artifact.
- `published_at` in the replay signals is the Wikinews revision timestamp, **not** authoritative event date.
- `release_order` drives deterministic replay — signals are released in index order.

---

## Key Design Decisions (locked)

- **No webhooks in v1**: use polling-style design. Public APIs like EONET/GDELT are polled.
- **Manual-first**: "Process Next Signal" button/endpoint. Autoplay is a later addition.
- **File = seed, DB = runtime state**: load JSON into DB once; track state in DB.
- **Live Gemini later**: AI calls happen live during demo, not pre-cached. Cached results only as fallback.
- **Impact radius from config, not AI**: Gemini extracts event/location/severity; backend applies `impact_rules.yaml` to determine affected client assets.

---

## What NOT to Build Until the Module Calls For It

- Gemini integration
- Client asset matching
- Alert generation
- React frontend / GraphQL
- EONET / GDELT connectors
- Autoplay
- Authentication

---

## Running Locally

```bash
cp .env.example .env
docker compose up --build
```

Then test at `http://localhost:8000`.
