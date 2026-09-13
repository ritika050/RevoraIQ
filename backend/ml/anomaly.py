from __future__ import annotations

from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    def __init__(self) -> None:
        self.model = IsolationForest(contamination=0.12, random_state=42, n_estimators=80)
        self.fitted = False

    def fit(self, amounts: list[float]) -> None:
        if len(amounts) < 8:
            self.fitted = False
            return
        x = np.array(amounts, dtype=float).reshape(-1, 1)
        self.model.fit(x)
        self.fitted = True

    def score(self, features: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        patterns: list[str] = []
        rule_score = 0.0
        amount = float(features["amount"])
        avg = float(profile.get("avg_amount") or 0)
        z = 0.0
        if avg:
            # Approximate z using a conservative std of 30% of mean when history is short.
            std = max(avg * 0.3, 1.0)
            z = abs(amount - avg) / std
        if z >= 3 or (avg and amount > avg * 8):
            patterns.append("Unusually high transaction amount")
            rule_score += 35
        if features.get("recent_frequency", 0) >= 4:
            patterns.append("High transaction frequency")
            rule_score += 20
        if features.get("is_new_device"):
            patterns.append("New device")
            rule_score += 15
        if features.get("is_new_location"):
            patterns.append("Location deviation")
            rule_score += 15
        if features.get("is_new_beneficiary"):
            patterns.append("New beneficiary")
            rule_score += 15
        if features.get("unusual_hour"):
            patterns.append("Unusual transaction time")
            rule_score += 8

        ml_score = 0.0
        if self.fitted:
            pred = self.model.decision_function(np.array([[amount]], dtype=float))[0]
            # IsolationForest: lower (more negative) is more anomalous.
            ml_score = float(max(0.0, min(100.0, (0.2 - pred) * 120)))
            if ml_score >= 55 and "Unusually high transaction amount" not in patterns:
                patterns.append("Isolation Forest flagged amount outlier")

        anomaly_score = int(max(0, min(100, round(max(rule_score, ml_score * 0.7 + rule_score * 0.5)))))
        is_anomaly = anomaly_score >= 45 or len(patterns) >= 2
        return {
            "anomaly_score": anomaly_score,
            "is_anomaly": is_anomaly,
            "patterns": patterns,
            "z_score": round(z, 2),
            "ml_score": round(ml_score, 2),
            "method": "isolation_forest+rules" if self.fitted else "rules+zscore",
        }
