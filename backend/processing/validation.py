from __future__ import annotations

from typing import Any

ALLOWED_SOURCES = {
    "transaction",
    "user_activity",
    "application_event",
    "api",
    "iot",
    "third_party",
    "system_log",
}


class EventValidationError(ValueError):
    pass


def validate_event(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise EventValidationError("Event payload must be an object")

    user_id = str(payload.get("user_id") or "").strip()
    if not user_id:
        raise EventValidationError("user_id is required")

    amount = payload.get("transaction_amount")
    try:
        amount = float(amount)
    except (TypeError, ValueError):
        raise EventValidationError("transaction_amount must be a number")
    if amount < 0:
        raise EventValidationError("transaction_amount cannot be negative")

    source = str(payload.get("source") or "transaction").strip().lower()
    if source not in ALLOWED_SOURCES:
        source = "transaction"

    cleaned = {
        "event_id": payload.get("event_id"),
        "user_id": user_id,
        "source": source,
        "event_type": str(payload.get("event_type") or "payment"),
        "transaction_amount": amount,
        "currency": str(payload.get("currency") or "INR"),
        "device_id": str(payload.get("device_id") or "DEV-UNKNOWN"),
        "location": str(payload.get("location") or "Unknown"),
        "beneficiary": str(payload.get("beneficiary") or "UNKNOWN"),
        "timestamp": payload.get("timestamp"),
        "metadata": payload.get("metadata") or {},
    }
    return cleaned
