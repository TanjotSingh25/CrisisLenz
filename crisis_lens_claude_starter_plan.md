# Crisis Lens - Claude Code Starter Plan

Last updated: 2026-05-29

This file is the starting context for Claude Code / Cursor. It defines the project direction, data decisions, architecture, and the first module to build. Do not build the whole application at once. Start with the Replay Feed Simulator.

---

## 1. Project Summary

**Project name:** Crisis Lens

**Project type:** AI-assisted signal-to-alert prototype

**Purpose:** Build a focused demo project related to public event intelligence, operational risk monitoring, and client-specific alerting. This is intended as a portfolio/demo project for re-engaging with Samdesk after a strong interview process.

**Important framing:** This is not a Samdesk clone. It is a small prototype showing the ability to design a signal ingestion pipeline, process noisy public event data, use AI for extraction/enrichment, and generate client-specific operational alerts.

**One-line description:**

> Crisis Lens ingests public-event/news signals, analyzes them with Gemini, matches events against sample client assets, and generates simulated operational-risk alerts.

---

## 2. High-Level Product Idea

Crisis Lens should simulate how public signals enter an intelligence system and become actionable client alerts.

Core workflow:

```text
Replay signal/article enters system
        ↓
Signal is released by simulator
        ↓
Crisis Lens ingests the released signal
        ↓
Gemini analyzes the signal live
        ↓
Structured event is created
        ↓
Event is matched against sample client assets
        ↓
Simulated alert is generated
        ↓
Dashboard shows source, event, impact, and suggested action
```

The immediate goal is not to finish the entire product. The immediate goal is to build the **Replay Feed Simulator**, which will provide controlled demo inputs for later AI/event/alert processing.

---

## 3. Current Locked Decisions

### Architecture

Use a **modular monolith**, not microservices.

Reason: this is a prototype/demo. Microservices add unnecessary complexity. Use clear internal modules instead.

Recommended stack:

```text
Backend: Python + FastAPI
Database: PostgreSQL
ORM: SQLAlchemy
Migrations: Alembic
API style: REST for operational commands; GraphQL later if useful for dashboard reads
AI: Gemini API, later module
Frontend: React + Vite + TypeScript, later module
Map: Leaflet + OpenStreetMap, later module
Auth: skip for v1 unless absolutely necessary
Deployment: local Docker first, deploy later
```

### Data-source strategy

Primary demo source:

```text
Filtered Wikinews replay dataset
```

Secondary source later:

```text
NASA EONET snapshots / optional live EONET connector
```

Optional source later:

```text
GDELT connector
```

Do not depend on live GDELT/EONET during the first demo. Live APIs are useful later but should not be required for demo reliability.

---

## 4. Current Input Data

The user has extracted and filtered Wikinews data.

Expected final replay file:

```text
data/replay/final_replay_signals.json
```

The file contains article-like JSON records.

Example record shape:

```json
{
  "source_type": "wikinews_dump",
  "source_name": "Wikinews",
  "title": "Example event article",
  "published_at": "2024-12-17T16:20:18Z",
  "summary": "Short summary text...",
  "body": "Cleaned article body text...",
  "language": "en",
  "url": "https://en.wikinews.org/wiki/Example_event_article",
  "filter_score": 22.4,
  "category_hint": "political_security",
  "matched_keywords": ["attack", "killed", "injured"]
}
```

Notes:

- `published_at` may be the Wikinews revision/page timestamp, not the actual event date.
- Do not treat the date as authoritative.
- The file is already filtered offline.
- It intentionally may contain a small number of low-value/noise articles so the later app can show rejection/triage behavior.
- Do not make the application parse the original Wikinews XML dump.
- The app should only consume the final prepared replay JSON.

---

## 5. Filtering Philosophy

The full Wikinews dump is too noisy for the live demo.

Filtering is an **offline data preparation step**, not the core demo.

Offline flow:

```text
Wikinews XML dump
        ↓
extract article-shaped records
        ↓
remove archive/index/interview junk
        ↓
score crisis/business-risk relevance
        ↓
create final_replay_signals.json
```

Runtime flow:

```text
final_replay_signals.json
        ↓
load into database
        ↓
simulator releases one signal at a time
```

The demo should not start from thousands of raw Wikinews articles. It should start from the prepared replay dataset.

---

## 6. Simulation Design

Build a **Replay Feed Simulator**.

This simulator represents the external world / signal provider. It is not fake news. It is a controlled replay feed for demo stability.

Professional framing:

> Crisis Lens uses a replayable signal-feed simulator for demo stability. The simulator exposes realistic public-signal payloads through the same ingestion pattern that live providers would use. In production, this provider layer could be replaced or extended with licensed news APIs, public safety feeds, RSS, GDELT, NASA EONET, and customer-specific intelligence feeds.

### Do not use webhooks in v1

Use manual control + polling-style design.

Reason:

- EONET/GDELT do not push data through webhooks.
- Public APIs are usually polled.
- Webhooks add unnecessary complexity: receiver endpoint, authentication, retries, duplicate handling.
- This prototype needs reliable demo behavior.

### Main v1 demo control

Use a button / endpoint concept:

```text
Process Next Signal
```

Each click releases one pending signal.

Flow:

```text
pending signal
        ↓ Process Next Signal
released signal
        ↓ later ingestion/AI module
processed or rejected
```

### Optional later mode

Add autoplay only after manual mode works:

```text
Start Replay
```

Every ~30 seconds, release/process one signal.

Do not build autoplay first.

---

## 7. Runtime Storage Decision

Use both file and database.

### File

The file is the portable seed source:

```text
data/replay/final_replay_signals.json
```

### Database

Load this file into PostgreSQL table:

```text
replay_signals
```

Do not read directly from the JSON file every time during the demo. Load it into the database first so state can be tracked cleanly.

Concept:

```text
File = seed/input source
Database = runtime simulator state
```

---

## 8. Replay Signal States

Use these statuses:

```text
pending
released
processed
rejected
```

Definitions:

- `pending`: loaded into simulator but not released yet.
- `released`: visible/available as a newly arrived signal.
- `processed`: later AI/event pipeline successfully handled it.
- `rejected`: later triage/AI decided it is not operationally relevant.

For Module 1, only `pending`, `released`, and reset behavior are required. `processed`/`rejected` can be included as allowed statuses but do not need full AI logic yet.

---

## 9. First Module to Build

## Module 1: Replay Feed Simulator

Build only this first.

Do not build Gemini integration yet.
Do not build client asset matching yet.
Do not build alert generation yet.
Do not build frontend dashboard yet except optional minimal health/status page if convenient.
Do not build EONET/GDELT connectors yet.

### Goal

Create a backend service that can:

1. Load `final_replay_signals.json` into PostgreSQL.
2. Store signals with status.
3. Release one signal at a time.
4. Show simulator status/counts.
5. Reset simulator state.
6. Expose released signals for later ingestion.

---

## 10. Suggested Database Table for Module 1

Create table:

```text
replay_signals
```

Suggested columns:

```text
id
source_type
source_name
title
published_at
summary
body
language
url
filter_score
category_hint
matched_keywords
status
release_order
released_at
processed_at
raw_payload
created_at
updated_at
```

Notes:

- Store full original JSON in `raw_payload`.
- Store `matched_keywords` as JSON/array.
- Use `release_order` so signals are processed in a stable deterministic order.
- Use UUID or integer primary key. Either is acceptable.
- Do not overcomplicate this.

---

## 11. Suggested API Endpoints for Module 1

Use REST for simulator operational commands.

### Health

```http
GET /health
```

Returns service status.

### Load replay data

```http
POST /replay/load
```

Behavior:

- Reads `data/replay/final_replay_signals.json`.
- Clears existing replay data or upserts depending on implementation.
- Inserts records into `replay_signals`.
- Sets status to `pending`.
- Assigns `release_order`.
- Returns count loaded.

Optional request body:

```json
{
  "reset_existing": true
}
```

### Replay status

```http
GET /replay/status
```

Returns counts:

```json
{
  "total": 100,
  "pending": 85,
  "released": 10,
  "processed": 4,
  "rejected": 1
}
```

### Release next signal

```http
POST /replay/next
```

Behavior:

- Finds next `pending` signal by `release_order`.
- Marks it `released`.
- Sets `released_at`.
- Returns the released signal.

If no pending signals remain, return a clear message.

### List released signals

```http
GET /replay/signals/released
```

Returns released signals. This is what a later ingestion pipeline can poll.

### List pending signals

```http
GET /replay/signals/pending
```

Useful for debugging.

### Reset replay

```http
POST /replay/reset
```

Behavior:

- Sets all signals back to `pending`.
- Clears `released_at` and `processed_at`.
- Does not delete the data.

Optional:

```http
DELETE /replay/clear
```

Clears replay table completely.

---

## 12. Expected Module 1 Behavior

After implementation, this should work:

```bash
POST /replay/load
GET /replay/status
POST /replay/next
GET /replay/signals/released
POST /replay/reset
```

Example status progression:

Initial after load:

```json
{
  "total": 100,
  "pending": 100,
  "released": 0,
  "processed": 0,
  "rejected": 0
}
```

After one `POST /replay/next`:

```json
{
  "total": 100,
  "pending": 99,
  "released": 1,
  "processed": 0,
  "rejected": 0
}
```

This proves the simulator works.

---

## 13. Suggested Project Folder Structure

Use a clean modular backend layout.

```text
crisis-lens/
  backend/
    app/
      main.py
      config.py
      database.py

      replay/
        models.py
        schemas.py
        service.py
        routes.py

      common/
        timestamps.py
        errors.py

    alembic/
    requirements.txt
    Dockerfile

  data/
    replay/
      final_replay_signals.json

  docker-compose.yml
  .env.example
  README.md
```

Keep Module 1 narrow. Do not add unnecessary folders yet.

---

## 14. Development Assumptions

The first version should run locally.

Use Docker Compose if possible:

```text
backend
postgres
```

Frontend can be omitted in Module 1 unless the coding assistant chooses to scaffold it lightly.

Minimum local commands should be:

```bash
docker compose up --build
```

Then verify:

```text
GET http://localhost:8000/health
POST http://localhost:8000/replay/load
GET http://localhost:8000/replay/status
POST http://localhost:8000/replay/next
```

---

## 15. Later Modules After Replay Simulator

After Module 1 works, continue in this order:

1. Raw signal ingestion pipeline.
2. Live Gemini signal-to-event analysis.
3. Config-file based impact-radius rules.
4. Sample clients and client assets.
5. Client impact matching using event location + radius.
6. Simulated alert generation.
7. GraphQL API for dashboard reads.
8. Clean React dashboard.
9. Optional NASA EONET snapshot/live connector.
10. Optional GDELT connector.
11. Optional replay autoplay.
12. Deployment.
13. README, screenshots, and short demo video.

---

## 16. Important Later Design Decision: AI + Impact Radius

Later, Gemini should be used live during the demo.

User preference:

```text
Use live Gemini calls during the demo.
Cached AI results may exist only as fallback.
```

Reason: live AI output makes the demo feel real and trustworthy.

Impact radius should not be freely invented by Gemini. Use this split:

```text
Gemini extracts/interprets:
- event type
- severity
- location
- business impact
- recommended action

Backend determines:
- impact radius
- affected client assets
- alert priority
```

Impact radius rules should live in config files, not hardcoded.

Example future file:

```text
config/impact_rules.yaml
```

This allows tuning by event type/severity and creates a good CFO/CTO pitch point:

> The AI interprets the signal, but client-impact matching is explainable and controlled through configurable operational rules.

Do not implement this in Module 1. Save for later.

---

## 17. What Not To Build in Module 1

Do not build:

```text
Gemini integration
event extraction
client matching
alert generation
frontend dashboard
map
GraphQL
EONET connector
GDELT connector
webhooks
autoplay
authentication
deployment polish
```

Only build the simulator foundation.

---

## 18. Claude Code Task for Module 1

Use this as the actual first coding instruction:

```text
Build Module 1 for Crisis Lens: the Replay Feed Simulator.

Create a Python/FastAPI backend with PostgreSQL that can load a prepared replay dataset from data/replay/final_replay_signals.json into a replay_signals table, track statuses, release one signal at a time, reset the replay, and expose status/count endpoints.

Use a modular monolith structure. Do not build Gemini integration, alert generation, frontend dashboard, GraphQL, EONET, or GDELT yet.

Required endpoints:
- GET /health
- POST /replay/load
- GET /replay/status
- POST /replay/next
- GET /replay/signals/released
- GET /replay/signals/pending
- POST /replay/reset

Use SQLAlchemy and Alembic. Use Docker Compose with backend and PostgreSQL. Include .env.example and clear README run instructions.

Data file shape:
Each record in data/replay/final_replay_signals.json contains source_type, source_name, title, published_at, summary, body, language, url, filter_score, category_hint, and matched_keywords.

Store the original record in raw_payload as well.
Set initial status to pending.
Use release_order for deterministic replay.
POST /replay/next should mark the next pending signal as released and return it.

Keep implementation clean and simple. This is only Module 1.
```

---

## 19. Success Criteria for Module 1

Module 1 is complete when:

- App starts locally.
- PostgreSQL connects successfully.
- `POST /replay/load` loads the JSON file.
- `GET /replay/status` shows counts.
- `POST /replay/next` releases one signal.
- `GET /replay/signals/released` shows the released signal.
- `POST /replay/reset` resets statuses to pending.
- No Gemini/API/dashboard code is included yet.
- README explains how to run and test the module.

---

## 20. Final Direction

Start with the Replay Feed Simulator. This is the correct first step because the entire project depends on having reliable, controlled incoming data. Once this module works, build the AI processing pipeline on top of it.
