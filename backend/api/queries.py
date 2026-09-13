from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.database.db import db_session


def list_events(filters: dict[str, Any]) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if filters.get("event_id"):
        clauses.append("e.event_id LIKE ?")
        params.append(f"%{filters['event_id']}%")
    if filters.get("user_id"):
        clauses.append("e.user_id LIKE ?")
        params.append(f"%{filters['user_id']}%")
    if filters.get("event_type"):
        clauses.append("e.event_type = ?")
        params.append(filters["event_type"])
    if filters.get("source"):
        clauses.append("e.source = ?")
        params.append(filters["source"])
    if filters.get("severity"):
        clauses.append("r.severity = ?")
        params.append(filters["severity"])
    if filters.get("anomaly") in {"true", "false"}:
        clauses.append("a.is_anomaly = ?")
        params.append(1 if filters["anomaly"] == "true" else 0)
    if filters.get("date"):
        clauses.append("substr(e.created_at, 1, 10) = ?")
        params.append(filters["date"])

    sql = f"""
        SELECT e.*, a.is_anomaly, a.anomaly_score, r.risk_score, r.severity, d.decision
        FROM events e
        LEFT JOIN anomalies a ON a.event_id = e.event_id
        LEFT JOIN risk_scores r ON r.event_id = e.event_id
        LEFT JOIN decisions d ON d.event_id = e.event_id
        WHERE {' AND '.join(clauses)}
        ORDER BY e.created_at DESC
        LIMIT 200
    """
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [_event_row(r) for r in rows]


def get_event_detail(event_id: str) -> dict[str, Any] | None:
    with db_session() as conn:
        event = conn.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
        if not event:
            return None
        processed = conn.execute("SELECT * FROM processed_events WHERE event_id = ?", (event_id,)).fetchone()
        anomaly = conn.execute(
            "SELECT * FROM anomalies WHERE event_id = ? ORDER BY id DESC LIMIT 1", (event_id,)
        ).fetchone()
        risk = conn.execute(
            "SELECT * FROM risk_scores WHERE event_id = ? ORDER BY id DESC LIMIT 1", (event_id,)
        ).fetchone()
        insight = conn.execute(
            "SELECT * FROM ai_insights WHERE event_id = ? ORDER BY id DESC LIMIT 1", (event_id,)
        ).fetchone()
        decision = conn.execute(
            "SELECT * FROM decisions WHERE event_id = ? ORDER BY id DESC LIMIT 1", (event_id,)
        ).fetchone()
        actions = conn.execute(
            "SELECT * FROM actions WHERE event_id = ? ORDER BY id DESC", (event_id,)
        ).fetchall()
        audits = conn.execute(
            "SELECT * FROM audit_logs WHERE event_id = ? ORDER BY id ASC", (event_id,)
        ).fetchall()
        profile = conn.execute(
            "SELECT * FROM behavior_profiles WHERE user_id = ?", (event["user_id"],)
        ).fetchone()

    pipeline = json.loads(processed["pipeline_json"]) if processed else {}
    return {
        "event": dict(event),
        "raw_event": json.loads(event["payload_json"]),
        "features": json.loads(processed["features_json"]) if processed else {},
        "behavior": pipeline.get("behavior"),
        "timeline": pipeline.get("timeline") or [],
        "anomaly": dict(anomaly) if anomaly else None,
        "risk": dict(risk) if risk else None,
        "insight": _insight(insight) if insight else None,
        "decision": dict(decision) if decision else None,
        "actions": [dict(a) for a in actions],
        "audit": [dict(a) for a in audits],
        "profile": _profile(profile) if profile else None,
    }


def list_alerts(status: str | None = None) -> list[dict[str, Any]]:
    sql = "SELECT * FROM alerts"
    params: list[Any] = []
    if status:
        sql += " WHERE status = ?"
        params.append(status)
    sql += " ORDER BY created_at DESC LIMIT 50"
    with db_session() as conn:
        rows = conn.execute(sql, params).fetchall()
        out = []
        for row in rows:
            item = dict(row)
            insight = conn.execute(
                "SELECT recommended_action, detected_patterns FROM ai_insights WHERE event_id = ? ORDER BY id DESC LIMIT 1",
                (row["event_id"],),
            ).fetchone()
            risk = conn.execute(
                "SELECT risk_score FROM risk_scores WHERE event_id = ? ORDER BY id DESC LIMIT 1",
                (row["event_id"],),
            ).fetchone()
            item["recommended_action"] = insight["recommended_action"] if insight else ""
            item["reasons"] = json.loads(insight["detected_patterns"]) if insight else []
            item["risk_score"] = risk["risk_score"] if risk else 0
            out.append(item)
        return out


def metrics() -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    minute_ago = (now - timedelta(minutes=1)).replace(microsecond=0).isoformat()
    with db_session() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM events").fetchone()["c"]
        epm = conn.execute(
            "SELECT COUNT(*) AS c FROM events WHERE created_at >= ?", (minute_ago,)
        ).fetchone()["c"]
        anomalies = conn.execute("SELECT COUNT(*) AS c FROM anomalies WHERE is_anomaly = 1").fetchone()["c"]
        high = conn.execute(
            "SELECT COUNT(*) AS c FROM risk_scores WHERE severity IN ('HIGH', 'CRITICAL')"
        ).fetchone()["c"]
        critical = conn.execute("SELECT COUNT(*) AS c FROM risk_scores WHERE severity = 'CRITICAL'").fetchone()["c"]
        actions = conn.execute("SELECT COUNT(*) AS c FROM actions").fetchone()["c"]

        events_over_time = conn.execute(
            """
            SELECT substr(created_at, 1, 16) AS bucket, COUNT(*) AS count
            FROM events
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT 24
            """
        ).fetchall()
        risk_dist = conn.execute(
            "SELECT severity, COUNT(*) AS count FROM risk_scores GROUP BY severity"
        ).fetchall()
        anomaly_trend = conn.execute(
            """
            SELECT substr(created_at, 1, 16) AS bucket, COUNT(*) AS count
            FROM anomalies
            WHERE is_anomaly = 1
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT 24
            """
        ).fetchall()
        amount_trend = conn.execute(
            """
            SELECT substr(created_at, 1, 16) AS bucket, AVG(transaction_amount) AS amount
            FROM events
            GROUP BY bucket
            ORDER BY bucket DESC
            LIMIT 24
            """
        ).fetchall()
        risk_by_user = conn.execute(
            """
            SELECT e.user_id, AVG(r.risk_score) AS avg_risk, COUNT(*) AS events
            FROM events e
            JOIN risk_scores r ON r.event_id = e.event_id
            GROUP BY e.user_id
            ORDER BY avg_risk DESC
            """
        ).fetchall()
        sources = conn.execute(
            "SELECT source, COUNT(*) AS count FROM events GROUP BY source"
        ).fetchall()

    return {
        "total_events": total,
        "events_per_minute": epm,
        "anomalies_detected": anomalies,
        "high_risk_events": high,
        "critical_events": critical,
        "actions_triggered": actions,
        "charts": {
            "events_over_time": [dict(r) for r in reversed(events_over_time)],
            "risk_distribution": [dict(r) for r in risk_dist],
            "anomaly_trend": [dict(r) for r in reversed(anomaly_trend)],
            "amount_trend": [dict(r) for r in reversed(amount_trend)],
            "risk_by_user": [dict(r) for r in risk_by_user],
            "sources": [dict(r) for r in sources],
        },
    }


def audit_logs(limit: int = 100) -> list[dict[str, Any]]:
    with db_session() as conn:
        rows = conn.execute(
            "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def system_status(pipeline) -> dict[str, Any]:
    return {
        "system": "healthy",
        "api": "up",
        "database": "up",
        "event_processor": "running",
        "ai_engine": "local" if not __import__("backend.config", fromlist=["OPENAI_API_KEY"]).OPENAI_API_KEY else "openai",
        "queue": pipeline.broker.snapshot(),
        "cache": pipeline.cache.stats(),
        "last_processed_event": pipeline.last_event_id,
        "total_events_processed": pipeline.processed_count,
        "failed_events": pipeline.failed_count,
        "demo_running": pipeline.demo_running,
    }


def _event_row(row) -> dict[str, Any]:
    return {
        "event_id": row["event_id"],
        "user_id": row["user_id"],
        "source": row["source"],
        "event_type": row["event_type"],
        "transaction_amount": row["transaction_amount"],
        "device_id": row["device_id"],
        "location": row["location"],
        "beneficiary": row["beneficiary"],
        "status": row["status"],
        "created_at": row["created_at"],
        "anomaly": bool(row["is_anomaly"]) if row["is_anomaly"] is not None else False,
        "anomaly_score": row["anomaly_score"],
        "risk_score": row["risk_score"] or 0,
        "severity": row["severity"] or "n/a",
        "decision": row["decision"] or "PENDING",
    }


def _insight(row) -> dict[str, Any]:
    item = dict(row)
    item["detected_patterns"] = json.loads(row["detected_patterns"] or "[]")
    return item


def _profile(row) -> dict[str, Any]:
    item = dict(row)
    for key in ("known_devices", "known_locations", "known_beneficiaries", "typical_hours"):
        item[key] = json.loads(row[key] or "[]")
    return item
