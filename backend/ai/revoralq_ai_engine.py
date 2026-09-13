from __future__ import annotations

import json
from typing import Any

from backend.config import OPENAI_API_KEY, OPENAI_MODEL


class RevoralQAIEngine:
    """Reasoning layer. Uses an LLM when OPENAI_API_KEY is set, otherwise local deterministic reasoning."""

    def analyze(
        self,
        event: dict[str, Any],
        profile: dict[str, Any],
        behavior: dict[str, Any],
        anomaly: dict[str, Any],
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        if OPENAI_API_KEY:
            try:
                return self._llm_reason(event, profile, behavior, anomaly, risk)
            except Exception:
                return self._local_reason(event, profile, behavior, anomaly, risk)
        return self._local_reason(event, profile, behavior, anomaly, risk)

    def _local_reason(
        self,
        event: dict[str, Any],
        profile: dict[str, Any],
        behavior: dict[str, Any],
        anomaly: dict[str, Any],
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        patterns = anomaly.get("patterns") or []
        amount = int(event.get("transaction_amount") or 0)
        user_id = event.get("user_id")
        severity = risk.get("severity", "LOW")
        deviation = behavior.get("deviation", "n/a")
        pattern_text = ", ".join(patterns) if patterns else "no strong anomaly patterns"

        if severity in {"HIGH", "CRITICAL"}:
            summary = (
                f"This transaction is highly unusual because the amount (₹{amount:,}) is significantly "
                f"higher than the user's historical average ({behavior.get('average')}). "
                f"The transaction also originated from a previously unseen device "
                f"({event.get('device_id')}) and was sent to a new beneficiary ({event.get('beneficiary')}). "
                f"Combined with the recent increase in transaction frequency, the event is classified as {severity.lower()} risk."
            )
            why = (
                f"User {user_id} typically transacts in {behavior.get('normal_range')}. "
                f"The current amount is {deviation}. Additional signals include {pattern_text}."
            )
            action = "Temporarily block the transaction and verify user identity before release."
            confidence = 0.94 if severity == "CRITICAL" else 0.88
        elif severity == "MEDIUM":
            summary = (
                f"User {user_id} produced a medium-risk event. Amount ₹{amount:,} is outside the usual "
                f"comfort zone ({behavior.get('normal_range')}) and some behavioral signals need monitoring."
            )
            why = f"Detected patterns: {pattern_text}."
            action = "Allow with enhanced monitoring and notify the risk analyst."
            confidence = 0.76
        else:
            summary = (
                f"User {user_id} completed a routine ₹{amount:,} payment consistent with historical behavior "
                f"({behavior.get('normal_range')})."
            )
            why = "Amount, device, location, and beneficiary align with the known profile."
            action = "Allow the transaction. No intervention required."
            confidence = 0.91

        return {
            "summary": summary,
            "why_it_happened": why,
            "detected_patterns": patterns,
            "risk_explanation": (
                f"Risk score {risk.get('risk_score')}/100 ({severity}) is driven by "
                f"{self._breakdown_text(risk)}."
            ),
            "recommended_action": action,
            "confidence": confidence,
            "engine": "local-deterministic",
        }

    def _llm_reason(
        self,
        event: dict[str, Any],
        profile: dict[str, Any],
        behavior: dict[str, Any],
        anomaly: dict[str, Any],
        risk: dict[str, Any],
    ) -> dict[str, Any]:
        from urllib import request

        prompt = {
            "event": event,
            "profile": profile,
            "behavior": behavior,
            "anomaly": anomaly,
            "risk": risk,
        }
        body = json.dumps(
            {
                "model": OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are the RevoralQ AI reasoning engine for real-time risk monitoring. "
                            "Return JSON with keys: summary, why_it_happened, detected_patterns, "
                            "risk_explanation, recommended_action, confidence."
                        ),
                    },
                    {"role": "user", "content": json.dumps(prompt)},
                ],
                "temperature": 0.2,
            }
        ).encode("utf-8")
        req = request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json",
            },
        )
        with request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        parsed["engine"] = "openai"
        parsed.setdefault("detected_patterns", anomaly.get("patterns") or [])
        parsed.setdefault("confidence", 0.9)
        return parsed

    @staticmethod
    def _breakdown_text(risk: dict[str, Any]) -> str:
        items = risk.get("breakdown") or {}
        if not items:
            return "no additive risk factors"
        return ", ".join(f"{key.replace('_', ' ')} +{value}" for key, value in items.items())
