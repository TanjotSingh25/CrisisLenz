# Crisis Lens Project Context and Simulation Plan

Last updated: May 26, 2026

This document captures the working plan, decisions, constraints, and context for the Crisis Lens prototype. It is meant to be saved and reused later as context for ChatGPT, Claude Code, Cursor, or any other coding assistant.

## 1. Project purpose

Crisis Lens is a portfolio/demo project intended for re-engaging with Samdesk after a strong interview process. The goal is not to build a Samdesk clone and not to imply that this is comparable to Samdesk's production platform.

The correct framing is:

> Crisis Lens is an AI-assisted signal-to-alert prototype that ingests public-event/news signals, analyzes them with Gemini, matches them against sample client assets, and generates client-specific operational risk alerts.

The project should show understanding of the domain: public signal ingestion, noisy data filtering, AI extraction, client impact matching, alert generation, and analyst-style review.

The project should help demonstrate initiative, backend/API ability, AI integration ability, and product thinking. It should not look desperate, copied, or overbuilt.

## 2. User goals and constraints

The user wants:

- A focused, impressive demo related to Samdesk's event-intelligence domain.
- A project that can be built quickly with Claude Code or Cursor.
- Step-by-step module prompts, not one giant prompt.
- A clean, polished UI, but not a fancy Apple-style marketing site.
- Python as the main backend language.
- Gemini API as the AI engine.
- GraphQL if it fits cleanly.
- A modular monolith, not microservices.
- A demo that works reliably and does not depend on random live news quality.
- Input data that can be simulated/replayed.
- Existing article data where possible, not manually writing dozens of fake articles.
- About 50-100 usable article/event inputs for the first version.
- Clear, narrow planning without overwhelming detail when not needed.

The user does not want:

- A Samdesk clone.
- A huge overengineered architecture.
- Web scraping as the core strategy.
- A dependency on unreliable or restricted news APIs.
- Manual writing of many synthetic articles.
- A giant response with too many implementation fields before the plan is locked.
- A default-looking, ugly 2010-style frontend.

## 3. Current locked architecture direction

Use a modular monolith.

Core stack:

- Backend: Python, FastAPI.
- Database: PostgreSQL.
- API: GraphQL using Strawberry if useful, plus REST for operational commands if needed.
- AI: Gemini API.
- Frontend: React, Vite, TypeScript.
- Map: Leaflet/OpenStreetMap if map functionality is used.
- Auth: skip or keep minimal for demo. Authentication is not central.
- Deployment: local first, deployed demo later.

Do not build microservices in v1. The project should have clean internal modules instead.

Potential internal modules:

- replay feed simulator
- ingestion pipeline
- AI analysis service
- event creation service
- client asset matching service
- alert generation service
- GraphQL API layer
- dashboard frontend

## 4. Current data/input decision

Primary input source for demo:

- Wikinews XML dump.

The user downloaded:

- `enwikinews-latest-pages-articles.xml.bz2`

This file is used to extract real Wikinews article pages into JSONL/JSON.

The current pipeline extracts articles from the XML dump, cleans wiki markup, filters archive/index pages, and produces a replay dataset.

Expected intermediate/output files:

- `all_wikinews_articles.jsonl` - all usable extracted Wikinews article pages.
- `filtered_replay_signals.json` - top filtered articles for demo replay.

The filtered dataset should contain roughly 50-100 article inputs, not necessarily all articles.

## 5. Article input format

The article records currently look roughly like this:

```json
{
  "source_type": "wikinews_dump",
  "source_name": "Wikinews",
  "title": "Article title",
  "published_at": "2026-04-25T13:56:45Z",
  "summary": "Short extracted summary",
  "body": "Cleaned article body text",
  "language": "en",
  "url": "https://en.wikinews.org/wiki/Article_Title",
  "filter_score": 16,
  "category_hint": "political_security",
  "matched_keywords": ["attack", "killed", "injured"]
}
```

Important note:

- `published_at` from the Wikinews dump may reflect page/revision timestamp, not the true event date.
- Date filtering is therefore imperfect and should not be treated as authoritative.
- For now, date issues can be ignored because this is a demo.

## 6. Filtering decisions

The initial keyword filter is acceptable for selecting demo data, but it is not meant to be production-grade.

The filter should keep articles related to:

- war
- conflict
- military incidents
- sanctions
- protests
- riots
- unrest
- attacks
- bombings
- explosions
- natural disasters
- emergency events
- transport disruption
- ports
- airports
- power outages
- strikes
- industrial incidents
- oil/chemical spills
- killed/injured/missing/damaged/evacuated indicators

The filter should penalize or exclude articles about:

- lunches/dinners
- routine meetings
- speeches
- ceremonies
- sports
- entertainment
- celebrities
- films/music/awards
- normal politics with no operational risk

Also exclude Wikinews index/archive/list pages such as:

- `Australia/2006`
- `Canada/2007`
- `United States/2008`
- other `Location/YYYY` pages
- pages containing many date lines
- pages containing index markers like `datenews`

This is important because one bad example, `Australia/2006`, scored very high due to containing many article headlines in one index page. It should not be treated as a single article.

Category assignment should be based on strongest category score, not first match.

Categories for first version:

- `natural_disaster`
- `political_security`
- `infrastructure`
- `industrial`
- `general_risk`

Mismatches are acceptable for v1. Gemini can correct/override later.

## 7. Secondary data sources

NASA EONET:

- Keep as a secondary structured natural-event connector.
- Useful for natural disaster/environmental events.
- Should not be the core AI story because EONET is already structured.
- Use either snapshots or live polling later.

GDELT:

- Keep as a secondary live/noisy news-signal connector later.
- Useful for global public signals, but noisy.
- Do not depend on GDELT for the guaranteed demo.
- Treat it as an optional connector showing source extensibility.

News APIs:

- Do not make restricted/free NewsAPI-style services the core deployed dependency.
- Local experimentation is fine, but final demo should not rely on a restricted API plan.

Manual article/text input:

- Optional later fallback feature.
- User can paste an article URL/text and run the AI analysis pipeline.

## 8. Simulation model decision

Use a Replay Feed Simulator.

The simulator represents the external world. It holds the Wikinews article inputs and releases them into the system in a controlled way.

Do not use webhooks in v1.

Reason:

- Webhooks mean the external source pushes data into Crisis Lens.
- EONET and GDELT do not work that way.
- Webhooks add unnecessary complexity: receiving endpoints, authentication, retries, duplicate handling, failure handling.
- Polling better matches the public API source model.

Use polling plus manual demo controls.

Main v1 demo mode:

- Button: `Process Next Signal`.
- Each click releases/ingests one new article/signal.
- The signal is analyzed by Gemini.
- An event is created.
- Matching against sample client assets happens.
- A simulated client alert appears.

Optional later mode:

- Button: `Start Replay`.
- Every 30 seconds, one new signal is released/processed automatically.
- This can make the dashboard feel live, but it is not needed for v1.

## 9. Replay source data vs processed app data

Keep source simulation data separate from processed product data.

Replay/source side:

- Stores raw article inputs.
- Represents what an external provider would send or expose.
- Has statuses like `pending`, `released`, `processed`.

Processed application side:

- Stores what Crisis Lens has created after ingestion/AI analysis.
- Includes raw signals, events, AI analysis results, client assets, and generated alerts.

Conceptual separation:

```text
Replay source data = external world / signal provider
Processed app data = Crisis Lens intelligence and alerts
```

## 10. Recommended simulation flow

Manual demo flow:

1. Dashboard starts empty or with a few old/sample alerts.
2. User clicks `Process Next Signal`.
3. Replay Feed Simulator releases the next pending article.
4. Crisis Lens ingestion pipeline polls/loads the released signal.
5. Gemini analyzes the signal.
6. Crisis Lens creates a structured event.
7. Crisis Lens checks sample client assets.
8. If relevant, Crisis Lens creates one or more simulated client alerts.
9. Dashboard shows the new alert and source article.

This is the core demo story:

```text
Article/signal enters -> AI extracts event -> client impact is matched -> alert is generated
```

## 11. Recommended first module to build

First build only the data simulation foundation.

Module name:

- Replay Feed Simulator

Build features:

- Load `filtered_replay_signals.json` into the database.
- Store replay articles with status.
- Show counts: pending, released, processed.
- Release next signal manually.
- Reset replay back to pending.
- Optionally release by category.

Suggested endpoints:

- `POST /replay/load`
- `POST /replay/next`
- `POST /replay/reset`
- `GET /replay/status`
- `GET /replay/signals/released`

The main application should not yet need Gemini for this first module. The goal is to prove that the input simulation works.

## 12. Later modules after simulation

After the Replay Feed Simulator works, continue in this order:

1. Replay Feed Simulator and database loading.
2. Raw signal ingestion pipeline.
3. Gemini signal-to-event analysis.
4. Client/asset seed data.
5. Client impact matching.
6. Alert generation.
7. GraphQL API.
8. Clean frontend dashboard.
9. Optional EONET connector.
10. Optional GDELT connector.
11. Optional autoplay mode.
12. Deployment.
13. README, screenshots, and 90-second demo video.

The project should be built module by module using Claude Code/Cursor prompts.

## 13. Frontend role

The frontend is for presentation. It is not the technical core, but it helps make the demo understandable quickly.

The UI should be:

- clean
- modern
- simple
- dashboard-like
- not ugly/default HTML
- not overly fancy

Likely views/components later:

- Replay controls
- Incoming signals
- Event/alert list
- Event detail panel
- Source evidence panel
- Client impact panel
- Map if useful

The user does not want to start by overdesigning the UI. It should come after the data simulation and backend flow are working.

## 14. How to explain the simulator professionally

Do not call it fake news.

Use this framing:

> Crisis Lens uses a replayable signal-feed simulator for demo stability. The simulator exposes realistic public-signal payloads through the same ingestion pattern that live providers would use. In production, this provider layer could be replaced or extended with licensed news APIs, public safety feeds, RSS, GDELT, NASA EONET, and customer-specific intelligence feeds.

This is honest and professional.

## 15. What to say this project is not

It is not:

- a Samdesk clone
- a production crisis-monitoring system
- a commercial news product
- a replacement for licensed intelligence feeds
- a fully reliable real-time alerting system

It is:

- a demo/prototype
- an AI-assisted signal-to-alert workflow
- a controlled replay-based public-signal analysis system
- a backend/API/AI integration portfolio project
- a way to show domain interest and technical initiative

## 16. Final current plan

Current next step:

Build the Replay Feed Simulator first.

Input:

- `filtered_replay_signals.json`

First goal:

- Load this file into the database.
- Simulate incoming public-event/news signals.
- Release one signal at a time manually.
- Expose status/counts.
- Prepare released signals for later AI analysis.

Do not add Gemini yet. Do not add GDELT/EONET yet. Do not add a full UI yet. Get the input simulation working first.
