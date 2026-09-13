from __future__ import annotations

from datetime import datetime
from typing import Any


def extract_features(event: dict[str, Any], profile: dict[str, Any], recent_count: int) -> dict[str, Any]:
    amount = float(event["transaction_amount"])
    avg_amount = float(profile.get("avg_amount") or 0)
    deviation = (amount / avg_amount) if avg_amount else amount
    hour = _hour(event.get("timestamp"))
    typical_hours = profile.get("typical_hours") or []
    return {
        "amount": amount,
        "avg_amount": round(avg_amount, 2),
        "amount_deviation": round(deviation, 2),
        "recent_frequency": recent_count,
        "is_new_device": event["device_id"] not in (profile.get("known_devices") or []),
        "is_new_location": event["location"] not in (profile.get("known_locations") or []),
        "is_new_beneficiary": event["beneficiary"] not in (profile.get("known_beneficiaries") or []),
        "unusual_hour": hour not in typical_hours if typical_hours else False,
        "hour": hour,
    }


def _hour(timestamp: str | None) -> int:
    if not timestamp:
        return datetime.utcnow().hour
    try:
        return datetime.fromisoformat(timestamp.replace("Z", "+00:00")).hour
    except ValueError:
        return datetime.utcnow().hour
