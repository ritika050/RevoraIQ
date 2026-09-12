from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.database.db import db_session


class ActionEngine:
    def execute(self, event_id: str, action_type: str, reason: str) -> dict[str, Any]:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        details = {
            "transaction": event_id,
            "action": action_type,
            "reason": reason,
            "status": "SUCCESS",
            "timestamp": now,
            "note": "Simulated action. No SMS or external side effects were sent.",
        }
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO actions (event_id, action_type, reason, status, details_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (event_id, action_type, reason, "SUCCESS", json.dumps(details), now),
            )
            conn.execute(
                "UPDATE events SET status = ? WHERE event_id = ?",
                ("actioned" if action_type != "ALLOW" else "processed", event_id),
            )
            if action_type in {"BLOCK_TRANSACTION", "FLAG_AND_ALERT", "CREATE_INCIDENT"}:
                conn.execute(
                    "UPDATE alerts SET status = ? WHERE event_id = ? AND status = 'open'",
                    ("actioned", event_id),
                )
            conn.execute(
                """
                INSERT INTO audit_logs (event_id, actor, action, details, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (event_id, "action_engine", action_type, json.dumps(details), now),
            )
        return details
