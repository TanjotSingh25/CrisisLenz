# Crisis Lens

> AI-assisted public signal intelligence and operational risk alerting — demo prototype.

Crisis Lens ingests public-event/news signals, analyzes them with Gemini, matches events against sample client assets, and generates simulated operational-risk alerts.

---

## Module 1: Replay Feed Simulator

The current module. Provides a controlled, deterministic signal feed that the rest of the pipeline will consume.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)

---

## Running Locally

```bash
# 1. Copy environment file
cp .env.example .env

# 2. Build and start
docker compose up --build
```

The API will be available at `http://localhost:8000`.

Interactive docs: `http://localhost:8000/docs`

---

## API — Module 1

### Health

```
GET /health
```

```json
{ "status": "ok" }
```

---

### Load replay data

Reads `data/replay/final_replay_signals.json` and seeds the database.

```
POST /replay/load
```

Optional body (defaults shown):
```json
{ "reset_existing": true }
```

Response:
```json
{ "loaded": 847 }
```

---

### Replay status

```
GET /replay/status
```

```json
{
  "total": 847,
  "pending": 846,
  "released": 1,
  "processed": 0,
  "rejected": 0
}
```

---

### Release next signal

Marks the next pending signal as `released` (ordered by `release_order`) and returns it.

```
POST /replay/next
```

Returns the released signal object. Returns 404 if no pending signals remain.

---

### List released signals

```
GET /replay/signals/released
```

Returns array of released signal objects. Used by later ingestion pipeline.

---

### List pending signals

```
GET /replay/signals/pending
```

Returns array of pending signal objects. Useful for debugging.

---

### Reset replay

Sets all signals back to `pending`. Clears `released_at` and `processed_at`. Does not delete data.

```
POST /replay/reset
```

---

### Clear replay table

Deletes all rows from the replay table.

```
DELETE /replay/clear
```

---

## Quick Test Sequence

```bash
curl -X POST http://localhost:8000/replay/load
curl http://localhost:8000/replay/status
curl -X POST http://localhost:8000/replay/next
curl http://localhost:8000/replay/signals/released
curl -X POST http://localhost:8000/replay/reset
```

---

## Project Structure

```
CrisisLenz/
  backend/
    app/
      main.py
      config.py
      database.py
      replay/          # Module 1
        models.py
        schemas.py
        service.py
        routes.py
      common/
        timestamps.py
        errors.py
    alembic/           # DB migrations
    requirements.txt
    Dockerfile
  data/
    replay/
      final_replay_signals.json
  docker-compose.yml
  .env.example
  CLAUDE.md
```

---

## Modules Roadmap

1. **Replay Feed Simulator** ← current
2. Raw signal ingestion pipeline
3. Live Gemini signal-to-event analysis
4. Config-driven impact radius rules
5. Sample clients + asset matching
6. Alert generation
7. React dashboard
