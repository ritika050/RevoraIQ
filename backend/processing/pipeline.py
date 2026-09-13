from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable

from backend.actions.action_engine import ActionEngine
from backend.ai.revoralq_ai_engine import RevoralQAIEngine
from backend.config import RAW_DIR
from backend.database.db import db_session, utcnow
from backend.decision.decision_engine import decide
from backend.ml.anomaly import AnomalyDetector
from backend.ml.behavior import BehaviorAnalyzer
from backend.ml.risk import score_risk
from backend.processing.features import extract_features
from backend.processing.validation import EventValidationError, validate_event
from backend.services.cache import InMemoryCache
from backend.services.event_queue import InMemoryBroker

PublishFn = Callable[[str, dict[str, Any]], Awaitable[None]]


class Pipeline:
    def __init__(self) -> None:
        self.broker = InMemoryBroker()
        self.cache = InMemoryCache()
        self.behavior = BehaviorAnalyzer()
        self.detector = AnomalyDetector()
        self.ai = RevoralQAIEngine()
        self.actions = ActionEngine()
        self.last_event_id: str | None = None
        self.processed_count = 0
        self.failed_count = 0
        self.publish: PublishFn | None = None
        self.demo_running = False
        self._fit_detector()

    def _fit_detector(self) -> None:
        with db_session() as conn:
            rows = conn.execute(
                "SELECT transaction_amount FROM events WHERE status = 'processed'"
            ).fetchall()
        amounts = [float(r["transaction_amount"] or 0) for r in rows]
        self.detector.fit(amounts)

    async def emit(self, event_type: str, payload: dict[str, Any]) -> None:
        if self.publish:
            await self.publish(event_type, payload)

    async def ingest(self, payload: dict[str, Any], auto_action_critical: bool = False) -> dict[str, Any]:
        try:
            await self.emit("pipeline", {"stage": "ingesting", "message": "Ingesting event..."})
            event = validate_event(payload)
            await self.emit("pipeline", {"stage": "validating", "message": "Validating..."})

            event_id = event.get("event_id") or f"EVT-{uuid.uuid4().hex[:8].upper()}"
            event["event_id"] = event_id
            event["timestamp"] = event.get("timestamp") or utcnow()

            self._ensure_user(event["user_id"])
            self._archive_raw(event)
            self._insert_raw_event(event)
            self.broker.publish("events.inbound", event)
            await self.emit(
                "pipeline",
                {
                    "stage": "queued",
                    "message": "Event queued on stream...",
                    "event_id": event_id,
                    "queue_size": self.broker.size("events.inbound"),
                },
            )

            queued = self.broker.consume("events.inbound")
            result = await self._process(queued or event, auto_action_critical=auto_action_critical)
            return result
        except EventValidationError as exc:
            self.failed_count += 1
            self._log_failure(payload, str(exc))
            await self.emit("pipeline", {"stage": "failed", "message": f"Validation failed: {exc}"})
            raise
        except Exception as exc:
            self.failed_count += 1
            self._log_failure(payload, str(exc))
            await self.emit("pipeline", {"stage": "failed", "message": f"Processing failed: {exc}"})
            raise

    async def _process(self, event: dict[str, Any], auto_action_critical: bool = False) -> dict[str, Any]:
        event_id = event["event_id"]
        user_id = event["user_id"]
        await self.emit("pipeline", {"stage": "processed", "message": "Running stream processing...", "event_id": event_id})

        profile = self.behavior.get_profile(user_id)
        recent_count = self._recent_frequency(user_id)
        features = extract_features(event, profile, recent_count)
        await self.emit("pipeline", {"stage": "features", "message": "Extracting features...", "event_id": event_id})

        await self.emit("pipeline", {"stage": "behavior", "message": "Analyzing behavior...", "event_id": event_id})
        comparison = self.behavior.compare(event, profile)

        await self.emit("pipeline", {"stage": "anomaly", "message": "Running anomaly detection...", "event_id": event_id})
        anomaly = self.detector.score(features, profile)

        await self.emit("pipeline", {"stage": "risk", "message": "Calculating risk...", "event_id": event_id})
        risk = score_risk(features, anomaly, comparison)

        await self.emit("pipeline", {"stage": "ai", "message": "RevoralQ AI reasoning...", "event_id": event_id})
        insight = self.ai.analyze(event, profile, comparison, anomaly, risk)

        await self.emit("pipeline", {"stage": "decision", "message": "Decision generated...", "event_id": event_id})
        decision = decide(risk, anomaly)

        now = utcnow()
        timeline = [
            {"stage": "EVENT", "at": event["timestamp"]},
            {"stage": "VALIDATED", "at": now},
            {"stage": "PROCESSED", "at": now},
            {"stage": "ANOMALY DETECTED" if anomaly["is_anomaly"] else "ANOMALY CLEAR", "at": now},
            {"stage": "RISK SCORED", "at": now},
            {"stage": "AI ANALYZED", "at": now},
            {"stage": "DECISION", "at": now},
        ]

        alert = None
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO processed_events (event_id, user_id, features_json, pipeline_json, processed_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    user_id,
                    json.dumps(features),
                    json.dumps({"timeline": timeline, "behavior": comparison}),
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO anomalies (event_id, anomaly_score, is_anomaly, patterns_json, method, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    anomaly["anomaly_score"],
                    1 if anomaly["is_anomaly"] else 0,
                    json.dumps(anomaly["patterns"]),
                    anomaly["method"],
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO risk_scores (event_id, risk_score, severity, breakdown_json, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, risk["risk_score"], risk["severity"], json.dumps(risk["breakdown"]), now),
            )
            conn.execute(
                """
                INSERT INTO ai_insights (
                    event_id, summary, why_it_happened, detected_patterns, risk_explanation,
                    recommended_action, confidence, engine, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event_id,
                    insight["summary"],
                    insight["why_it_happened"],
                    json.dumps(insight["detected_patterns"]),
                    insight["risk_explanation"],
                    insight["recommended_action"],
                    insight["confidence"],
                    insight.get("engine", "local-deterministic"),
                    now,
                ),
            )
            conn.execute(
                """
                INSERT INTO decisions (event_id, decision, rationale, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (event_id, decision["decision"], decision["rationale"], now),
            )
            conn.execute("UPDATE events SET status = ? WHERE event_id = ?", ("processed", event_id))
            conn.execute(
                """
                INSERT INTO audit_logs (event_id, actor, action, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, "pipeline", "process_event", json.dumps({"decision": decision["decision"]}), now),
            )

            if risk["severity"] in {"HIGH", "CRITICAL"}:
                conn.execute(
                    """
                    INSERT INTO alerts (event_id, user_id, severity, title, message, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        user_id,
                        risk["severity"],
                        f"{risk['severity']} RISK DETECTED",
                        insight["summary"],
                        "open",
                        now,
                    ),
                )
                alert = {
                    "event_id": event_id,
                    "user_id": user_id,
                    "severity": risk["severity"],
                    "risk_score": risk["risk_score"],
                    "reasons": anomaly["patterns"],
                    "recommendation": insight["recommended_action"],
                    "status": "open",
                }

        if decision["decision"] == "ALLOW":
            self.behavior.rebuild_profile(user_id)

        action_result = None
        if auto_action_critical and decision["decision"] == "BLOCK":
            await self.emit("pipeline", {"stage": "action", "message": "Action triggered...", "event_id": event_id})
            action_result = self.actions.execute(event_id, decision["action_type"], decision["rationale"])
            timeline.append({"stage": "ACTION", "at": utcnow()})

        self.last_event_id = event_id
        self.processed_count += 1
        self.cache.set(f"event:{event_id}", event_id, ttl=300)

        result = {
            "event": event,
            "features": features,
            "behavior": comparison,
            "anomaly": anomaly,
            "risk": risk,
            "insight": insight,
            "decision": decision,
            "alert": alert,
            "action": action_result,
            "timeline": timeline,
            "status": "actioned" if action_result else "processed",
        }
        await self.emit("event", self._feed_item(result))
        if alert:
            await self.emit("alert", alert)
        await self.emit("metrics", {"processed": self.processed_count})
        await self.emit(
            "pipeline",
            {
                "stage": "complete",
                "message": f"Completed {event_id} → {decision['decision']} ({risk['severity']})",
                "event_id": event_id,
            },
        )
        return result

    def _feed_item(self, result: dict[str, Any]) -> dict[str, Any]:
        event = result["event"]
        return {
            "event_id": event["event_id"],
            "user_id": event["user_id"],
            "source": event["source"],
            "transaction_amount": event["transaction_amount"],
            "created_at": event["timestamp"],
            "anomaly": result["anomaly"]["is_anomaly"],
            "anomaly_score": result["anomaly"]["anomaly_score"],
            "risk_score": result["risk"]["risk_score"],
            "severity": result["risk"]["severity"],
            "decision": result["decision"]["decision"],
            "status": result["status"],
            "recommended_action": result["insight"]["recommended_action"],
        }

    def _ensure_user(self, user_id: str) -> None:
        with db_session() as conn:
            row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if row:
                return
            conn.execute(
                """
                INSERT INTO users (user_id, name, email, city, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, user_id, f"{user_id.lower()}@example.com", "Unknown", "active", utcnow()),
            )

    def _insert_raw_event(self, event: dict[str, Any]) -> None:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO events (
                    event_id, user_id, source, event_type, transaction_amount, currency,
                    device_id, location, beneficiary, payload_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event["event_id"],
                    event["user_id"],
                    event["source"],
                    event["event_type"],
                    event["transaction_amount"],
                    event["currency"],
                    event["device_id"],
                    event["location"],
                    event["beneficiary"],
                    json.dumps(event),
                    "received",
                    event["timestamp"],
                ),
            )

    def _archive_raw(self, event: dict[str, Any]) -> None:
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        path = Path(RAW_DIR) / f"{event['event_id']}.json"
        path.write_text(json.dumps(event, indent=2), encoding="utf-8")

    def _recent_frequency(self, user_id: str) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=2)).replace(microsecond=0).isoformat()
        with db_session() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM events WHERE user_id = ? AND created_at >= ?",
                (user_id, cutoff),
            ).fetchone()
        return int(row["c"] if row else 0)

    def _log_failure(self, payload: dict[str, Any], error: str) -> None:
        with db_session() as conn:
            conn.execute(
                "INSERT INTO failed_events (payload_json, error, created_at) VALUES (?, ?, ?)",
                (json.dumps(payload), error, utcnow()),
            )
            conn.execute(
                "INSERT INTO audit_logs (event_id, actor, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
                (None, "pipeline", "failed_event", error, utcnow()),
            )
