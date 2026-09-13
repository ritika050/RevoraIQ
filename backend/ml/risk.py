from __future__ import annotations

from typing import Any

RISK_WEIGHTS = {
    "amount": 25,
    "frequency": 20,
    "new_device": 15,
    "new_location": 15,
    "new_beneficiary": 15,
    "behavior": 10,
}


def score_risk(features: dict[str, Any], anomaly: dict[str, Any], behavior: dict[str, Any]) -> dict[str, Any]:
    breakdown: dict[str, int] = {}
    total = 0

    if "Unusually high transaction amount" in anomaly.get("patterns", []) or features.get("amount_deviation", 0) >= 8:
        breakdown["amount_anomaly"] = RISK_WEIGHTS["amount"]
        total += RISK_WEIGHTS["amount"]
    if "High transaction frequency" in anomaly.get("patterns", []) or features.get("recent_frequency", 0) >= 4:
        breakdown["frequency_anomaly"] = RISK_WEIGHTS["frequency"]
        total += RISK_WEIGHTS["frequency"]
    if features.get("is_new_device"):
        breakdown["new_device"] = RISK_WEIGHTS["new_device"]
        total += RISK_WEIGHTS["new_device"]
    if features.get("is_new_location"):
        breakdown["new_location"] = RISK_WEIGHTS["new_location"]
        total += RISK_WEIGHTS["new_location"]
    if features.get("is_new_beneficiary"):
        breakdown["new_beneficiary"] = RISK_WEIGHTS["new_beneficiary"]
        total += RISK_WEIGHTS["new_beneficiary"]
    if behavior.get("deviation_value", 0) >= 5:
        breakdown["behavior_deviation"] = RISK_WEIGHTS["behavior"]
        total += RISK_WEIGHTS["behavior"]

    # Blend with ML anomaly score without exceeding 100.
    blended = min(100, max(total, int(round(anomaly.get("anomaly_score", 0) * 0.9))))
    severity = severity_from_score(blended)
    return {
        "risk_score": blended,
        "severity": severity,
        "breakdown": breakdown,
    }


def severity_from_score(score: int) -> str:
    if score <= 30:
        return "LOW"
    if score <= 60:
        return "MEDIUM"
    if score <= 80:
        return "HIGH"
    return "CRITICAL"
