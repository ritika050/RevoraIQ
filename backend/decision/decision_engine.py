from __future__ import annotations

from typing import Any


def decide(risk: dict[str, Any], anomaly: dict[str, Any]) -> dict[str, Any]:
    severity = risk.get("severity", "LOW")
    score = int(risk.get("risk_score") or 0)

    if severity == "CRITICAL" or score >= 81:
        return {
            "decision": "BLOCK",
            "action_type": "BLOCK_TRANSACTION",
            "rationale": "Critical risk: block/restrict the activity, raise an alert, and create an incident.",
        }
    if severity == "HIGH" or score >= 61:
        return {
            "decision": "FLAG",
            "action_type": "FLAG_AND_ALERT",
            "rationale": "High risk: flag the event and alert the operations team.",
        }
    if severity == "MEDIUM" or score >= 31:
        return {
            "decision": "MONITOR",
            "action_type": "MONITOR",
            "rationale": "Medium risk: allow with monitoring.",
        }
    return {
        "decision": "ALLOW",
        "action_type": "ALLOW",
        "rationale": "Low risk: allow the activity.",
    }
