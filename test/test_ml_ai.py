from backend.ml.anomaly import AnomalyDetector
from backend.ai.revoralq_ai_engine import RevoralQAIEngine


def test_anomaly_detector_flags_spike():
    detector = AnomalyDetector()
    detector.fit([500, 800, 1200, 700, 950, 1100, 650, 720, 880, 1000])
    features = {
        "amount": 75000,
        "recent_frequency": 5,
        "is_new_device": True,
        "is_new_location": True,
        "is_new_beneficiary": True,
        "unusual_hour": False,
    }
    profile = {"avg_amount": 850}
    result = detector.score(features, profile)
    assert result["is_anomaly"] is True
    assert result["anomaly_score"] >= 45
    assert "Unusually high transaction amount" in result["patterns"]
    assert "New device" in result["patterns"]


def test_local_ai_reasoning_is_human_readable():
    engine = RevoralQAIEngine()
    insight = engine.analyze(
        {
            "user_id": "USR-102",
            "transaction_amount": 75000,
            "device_id": "DEV-NEW-91",
            "beneficiary": "NEW-BEN-99",
        },
        {"avg_amount": 850},
        {
            "normal_range": "₹500 - ₹1,200",
            "average": "₹850",
            "deviation": "88x higher",
            "deviation_value": 88,
        },
        {
            "patterns": ["Unusually high transaction amount", "New device", "New beneficiary"],
            "anomaly_score": 90,
        },
        {"risk_score": 92, "severity": "CRITICAL", "breakdown": {"amount_anomaly": 25, "new_device": 15}},
    )
    assert "highly unusual" in insight["summary"].lower() or "unusual" in insight["summary"].lower()
    assert insight["recommended_action"]
    assert insight["confidence"] > 0.8
    assert insight["engine"] == "local-deterministic"
