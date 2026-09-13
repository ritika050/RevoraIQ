# RevoralQ architecture

RevoralQ is a layered monitoring system. Every layer in this document has a working implementation in the prototype, or a deliberate lightweight simulation with a real interface.

```
DATA SOURCES
      ↓
DATA INGESTION
      ↓
PROCESSING + AI/ML
      ↓
DATA STORAGE
      ↓
APPLICATION / DASHBOARD
      ↓
ACTION & INTEGRATION
      ↓
MONITORING & OPS
```

## 1. Data sources

The prototype focuses on **transaction / user activity** events so the demo is easy to follow. The source field still models the broader world:

- User activities
- Transactions
- System logs
- Application events
- APIs / external services
- IoT / devices
- Third-party data

The dashboard generator creates realistic INR payments for `USR-102` (normal ₹500–₹1,200, then a ₹75,000 spike).

## 2. Data ingestion

Implemented in `backend/processing/pipeline.py` and `backend/api`.

- **Real-time ingestion:** `POST /api/events` and generator endpoints.
- **Message broker / event queue:** `InMemoryBroker` in `backend/services/event_queue.py`. It exposes `publish` / `consume` so a Kafka client can be swapped in later (`KafkaBroker` placeholder).
- **Batch ingestion:** burst generation and demo sequence process multiple events in order.
- **Validation & filtering:** `backend/processing/validation.py`.
- **Schema / metadata:** Pydantic models plus SQLite schema in `backend/database/schema.sql`.
- **Raw archive:** each accepted payload is written to `data/raw/{event_id}.json` as a stand-in for object storage.

## 3. Processing and AI/ML

Stream processing consumes the inbound topic immediately (single-process simulation of a stream worker).

1. Feature extraction (`backend/processing/features.py`)
2. Behavior analysis (`backend/ml/behavior.py`)
3. Anomaly detection (`backend/ml/anomaly.py`) — Isolation Forest on amounts plus z-score / rule signals
4. Risk scoring (`backend/ml/risk.py`)
5. RevoralQ AI reasoning (`backend/ai/revoralq_ai_engine.py`)
6. Decision engine (`backend/decision/decision_engine.py`)

### Insights and reasoning

The AI engine receives the event, user profile, anomaly score, risk score, patterns, and historical comparison. It returns:

- summary
- why it happened
- detected patterns
- risk explanation
- recommended action
- confidence

If `OPENAI_API_KEY` is set, the engine asks an LLM to produce the same JSON. Any LLM failure falls back to the local engine so the product never depends on a key.

### Decision engine

| Severity | Score | Decision |
| --- | --- | --- |
| LOW | 0–30 | Allow |
| MEDIUM | 31–60 | Monitor |
| HIGH | 61–80 | Flag + alert |
| CRITICAL | 81–100 | Block + alert + incident |

## 4. Data storage

- **Raw store:** filesystem JSON archive
- **Processed / queryable store:** SQLite
- **NoSQL-style documents:** JSON columns for features, patterns, pipeline timeline
- **Cache:** `InMemoryCache` with TTL
- **Model store:** Isolation Forest held in the process; retrained from processed amounts at startup

## 5. Application and interface

React dashboard (`frontend/`):

- Real-time Intelligence Dashboard
- Alerts and notifications
- Search and analysis
- Event details with pipeline timeline
- Admin / ops health
- Audit logs

Live updates use Server-Sent Events (`GET /api/stream`).

## 6. Action and integration

`ActionEngine` writes an action log instead of sending SMS or moving money:

- Send alert
- Flag user / event
- Block transaction
- Create incident
- Simulated webhook payload in `details_json`

`Execute Recommended Action` always produces a visible SUCCESS record.

## 7. Monitoring and operations

- Application logs via uvicorn
- Audit logs table
- `/api/health` and `/api/admin/status`
- Failed-event table for invalid payloads
- Queue depth and last processed event on the Admin page

## Prototype vs production

| Production idea | Prototype choice |
| --- | --- |
| Kafka | In-memory broker + Kafka interface |
| Redis | In-memory cache |
| S3 / Blob | Local `data/raw` |
| Multi-node stream workers | Async pipeline in FastAPI |
| Online LLM | Optional; local reasoning always works |
