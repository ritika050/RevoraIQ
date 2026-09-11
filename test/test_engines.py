from backend.decision.decision_engine import decide
from backend.ml.risk import score_risk, severity_from_score
from backend.processing.validation import EventValidationError, validate_event


def test_validate_event_ok():
    event = validate_event(
        {
            "user_id": "USR-102",
            "transaction_amount": 500,
            "source": "transaction",
        }
    )
    assert event["user_id"] == "USR-102"
    assert event["transaction_amount"] == 500


def test_validate_event_rejects_missing_user():
    try:
        validate_event({"transaction_amount": 10})
        assert False, "expected error"
    except EventValidationError:
        pass


def test_severity_bands():
    assert severity_from_score(10) == "LOW"
    assert severity_from_score(45) == "MEDIUM"
    assert severity_from_score(70) == "HIGH"
    assert severity_from_score(92) == "CRITICAL"


def test_risk_scoring_suspicious_signals():
    features = {
        "amount_deviation": 37,
        "recent_frequency": 5,
        "is_new_device": True,
        "is_new_location": True,
        "is_new_beneficiary": True,
    }
    anomaly = {
        "anomaly_score": 88,
        "patterns": [
            "Unusually high transaction amount",
            "High transaction frequency",
            "New device",
            "Location deviation",
            "New beneficiary",
        ],
    }
    behavior = {"deviation_value": 37}
    risk = score_risk(features, anomaly, behavior)
    assert risk["risk_score"] >= 81
    assert risk["severity"] == "CRITICAL"


def test_decision_critical_blocks():
    decision = decide({"severity": "CRITICAL", "risk_score": 92}, {"is_anomaly": True})
    assert decision["decision"] == "BLOCK"
    assert decision["action_type"] == "BLOCK_TRANSACTION"


def test_decision_low_allows():
    decision = decide({"severity": "LOW", "risk_score": 12}, {"is_anomaly": False})
    assert decision["decision"] == "ALLOW"
