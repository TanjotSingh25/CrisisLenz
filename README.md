# Crisis Lens

> AI-assisted public signal intelligence and operational risk alerting — demo prototype.

Crisis Lens ingests public-event/news signals, analyzes them with Gemini, matches events against sample client assets, and generates simulated operational-risk alerts.

---

## Pipeline (modules built)

```
Replay signal → Gemini analysis → Structured event → Client impact matching → Simulated alert → Dashboard
```

1. **Replay Feed Simulator** — deterministic Wikinews + EONET signal feed
2. **EONET Snapshot Provider** — NASA natural-event data
3. **Gemini Live Signal Analysis** — extracts structured events, rejects noise
4. **Client Assets + Impact Matching** — config-driven impact-radius zones
5. **Simulated Alert Generation** — client-facing alerts from impact matches
6. **Operations Dashboard** — React/Vite step-by-step demo UI

Full details: [docs/architecture.md](docs/architecture.md) · Testing: [docs/testing.md](docs/testing.md)

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- A Gemini API key (for Module 3 analysis) — [Google AI Studio](https://aistudio.google.com/app/apikey)
- Node.js 18+ (only if running the dashboard outside Docker)

---

## Running Locally

```bash
# 1. Copy environment file and add your GEMINI_API_KEY
cp .env.example .env

# 2. Build and start the full stack (db + backend + dashboard)
docker compose up --build
```

- Dashboard: `http://localhost:5173`
- API: `http://localhost:8000`
- Interactive API docs: `http://localhost:8000/docs`

### Dashboard outside Docker (dev mode)

```bash
cd frontend
cp .env.example .env     # defaults to http://localhost:8000
npm install
npm run dev              # http://localhost:5173
```

---

## Security Notes

Crisis Lens is a demo prototype, not a production incident-intelligence system. It includes a basic, practical hardening pass:

- **Backend-only Gemini API key** — the key lives only in the backend `.env`; it is never exposed to the browser. The frontend only ever receives `VITE_API_BASE_URL`.
- **Environment-based configuration** — secrets come from environment variables; nothing is hardcoded. `.env` is gitignored; `.env.example` ships with blank values.
- **Restricted CORS** — no wildcard. Allowed origins come from `ALLOWED_ORIGINS`.
- **Optional admin token** — set `DEMO_ADMIN_TOKEN` to require `X-Demo-Admin-Token` on all mutation endpoints (POST/PUT/PATCH/DELETE). Empty by default for local demos. Never put this in the frontend.
- **Validated inputs** — source type, alert status, and severity filters are restricted to known enum values (invalid values get a 422).
- **Clean errors** — in `production`, API responses never leak stack traces or internals; full tracebacks go to the backend logs only.
- **No secret logging** — keys, tokens, and DB URLs are never logged; model output is logged only as a bounded preview.
- **Prompt-injection guardrails** — the system prompt treats article text as untrusted and never follows instructions embedded in it.
- **Frontend hygiene** — no `dangerouslySetInnerHTML`, article text rendered as plain text, external links use `rel="noopener noreferrer"`, no secrets in `localStorage`.
- **Simulated alerting only** — no real email/Slack/SMS/webhook delivery.

Run a quick secret-leak scan over tracked files:
```bash
bash scripts/check_no_secrets.sh
```

### Deployment checklist

Before deploying publicly:

- [ ] `.env` is **not** committed (verify with `git status` and `scripts/check_no_secrets.sh`)
- [ ] `GEMINI_API_KEY` and `DATABASE_URL` are set **only** on the backend host
- [ ] `ENVIRONMENT=production` on the backend (hides error detail, fails fast on missing secrets)
- [ ] `ALLOWED_ORIGINS` lists **only** the deployed frontend URL
- [ ] `DEMO_ADMIN_TOKEN` is set (and supplied via the `X-Demo-Admin-Token` header) if the deployment is public
- [ ] Frontend build receives **only** `VITE_API_BASE_URL` — no secret `VITE_*` vars
- [ ] No raw secrets appear in the frontend bundle

Typical split: frontend on Vercel/Netlify (only `VITE_API_BASE_URL`); backend on Render/Railway/Fly (Gemini key, database URL, admin token).

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
