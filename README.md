# RevoralQ

**Real-Time AI Monitoring & Intelligence**

RevoralQ is a working prototype of an AI-powered monitoring platform. It ingests activity and transaction events, detects anomalies, scores risk, explains what happened in plain language, then decides and executes simulated actions.

No API key is required. If `OPENAI_API_KEY` is present, explanations can be enhanced with an LLM. Otherwise the local RevoralQ AI engine is used automatically.

## Problem

Modern systems generate a constant stream of user activity, payments, logs, device events, and third-party callbacks. Traditional monitoring tools can show charts and fire static threshold alerts, but they rarely explain *why* something is risky or what to do next. Analysts are left stitching context together after the incident.

## Solution

RevoralQ runs a visible end-to-end pipeline:

**Data sources → ingestion → validation → event stream → feature extraction → anomaly detection → behavior analysis → risk scoring → AI reasoning → decision → storage → dashboard → action.**

The Intelligence Dashboard is designed for a five-minute live demo: generate normal payments, inject a ₹75,000 spike from a new device and beneficiary, watch the pipeline stages, then execute the recommended block.

## Key features

- Real-time and burst event generation
- Isolation Forest + rule-based anomaly detection
- Per-user behavior profiles
- Transparent risk scoring (0–100) with LOW / MEDIUM / HIGH / CRITICAL bands
- RevoralQ AI reasoning engine (LLM optional, local fallback always on)
- Decision engine (Allow / Monitor / Flag / Block)
- Simulated actions with an action log (no real SMS or funds movement)
- Live dashboard, alerts, search, event details, audit, and admin health
- Server-Sent Events for live UI updates
- Demo Mode (~60–120 seconds) for pitch recordings

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

```
DATA SOURCES → INGESTION → PROCESSING + AI/ML → STORAGE
        → DASHBOARD → ACTION & INTEGRATION → MONITORING
```

## Tech stack

| Layer | Choice |
| --- | --- |
| Frontend | React, Vite, Tailwind CSS, Recharts |
| Backend | Python, FastAPI |
| Database | SQLite |
| Cache | In-memory (Redis-replaceable) |
| Streaming | In-memory EventBroker (Kafka-compatible interface) |
| ML | scikit-learn Isolation Forest, statistical rules |
| Reasoning | Local deterministic engine, optional OpenAI |

## Data flow

1. Event generator or `POST /events` submits a payload.
2. Validation and schema cleanup run.
3. Raw JSON is archived under `data/raw/`.
4. The event is published to the in-memory broker and consumed by stream processing.
5. Features are extracted against the user behavior profile.
6. Anomaly detection and risk scoring run.
7. RevoralQ AI produces a human-readable explanation.
8. The decision engine chooses Allow / Monitor / Flag / Block.
9. Results are stored in SQLite and pushed to the dashboard over SSE.
10. Operators (or Demo Mode) execute the recommended action.

## AI/ML approach

- **Behavior profile:** average / min / max amount, known devices, locations, beneficiaries, typical hours.
- **Anomaly score:** Isolation Forest on historical amounts plus rules for amount deviation, frequency, new device / location / beneficiary.
- **Risk score:** additive, capped at 100:
  - Amount anomaly +25
  - Frequency anomaly +20
  - New device +15
  - New location +15
  - New beneficiary +15
  - Behavior deviation +10
- **Reasoning:** structured narrative from scores and patterns; optional LLM rewrite.

## Database design

Tables: `users`, `events`, `processed_events`, `behavior_profiles`, `anomalies`, `risk_scores`, `ai_insights`, `decisions`, `actions`, `alerts`, `audit_logs`, `failed_events`.

Schema is applied automatically on startup. Seed data loads four users including **USR-102 (Ananya Rao)** with a normal ₹500–₹1,200 history.

## API documentation

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health + component status |
| POST | `/api/events` | Ingest an event |
| POST | `/api/events/generate` | `normal` / `suspicious` / `burst` |
| POST | `/api/demo/run` | Paced Demo Mode |
| POST | `/api/demo/scenario` | Faster demo scenario |
| GET | `/api/events` | List / search |
| GET | `/api/events/{event_id}` | Full event detail |
| GET | `/api/alerts` | Incident panel |
| GET | `/api/metrics` | KPI + chart payloads |
| GET | `/api/users/{user_id}/profile` | Behavior profile |
| GET | `/api/insights/{event_id}` | AI insight |
| POST | `/api/actions/{event_id}/execute` | Execute recommended action |
| POST | `/api/alerts/{event_id}/dismiss` | Dismiss alert |
| GET | `/api/audit-logs` | Audit trail |
| GET | `/api/admin/status` | Ops view |
| GET | `/api/stream` | Server-Sent Events |

## How to run locally

**Prerequisites:** Python 3.11+, Node.js 18+ (npm).

Windows:

```bat
run.bat
```

macOS / Linux:

```bash
chmod +x run.sh
./run.sh
```

Manual:

```bash
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r backend/requirements.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173) for the dashboard and [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) for the API.

## Environment variables

Copy `.env.example` to `.env` if you need overrides.

| Variable | Default | Notes |
| --- | --- | --- |
| `OPENAI_API_KEY` | empty | Optional LLM reasoning |
| `OPENAI_MODEL` | `gpt-4o-mini` | Used only if a key is set |
| `DATABASE_PATH` | `data/revoralq.db` | SQLite file |
| `RAW_ARCHIVE_PATH` | `data/raw` | Raw event archive |
| `FRONTEND_ORIGIN` | `http://localhost:5173` | CORS |

## Demo instructions

1. Start backend and frontend.
2. Open the Intelligence Dashboard.
3. Click **DEMO MODE** and leave it running for about 60–120 seconds.
4. Watch the live pipeline, event feed, charts, and critical alert.
5. Click **Execute Action** if Demo Mode has not already auto-blocked the spike.
6. Open the event detail page for the ₹75,000 transaction.

Exact click-path: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).  
Spoken pitch: [docs/PITCH_SCRIPT.md](docs/PITCH_SCRIPT.md).

## Screenshots

Add demo captures here after recording:

- `docs/screenshots/dashboard.png`
- `docs/screenshots/alert.png`
- `docs/screenshots/event-detail.png`

## Tests

```bash
.venv\Scripts\python -m pytest -q
```

Coverage includes validation, anomaly detection, risk scoring, decisions, local reasoning, and API generate/health.

## Future enhancements

- Replace InMemoryBroker with Kafka (`backend/services/event_queue.py` already defines the interface)
- Redis cache instead of in-memory TTL cache
- Object storage (S3 / Azure Blob) behind the raw archive writer
- Online learning for Isolation Forest
- Role-based access control and SSO
- True webhook delivery with retry queues

## License

Prototype for demonstration and evaluation.
