from fastapi.testclient import TestClient

from backend.database.db import init_database, seed_database
from backend.main import app


def test_health_and_generate():
    init_database()
    seed_database()
    with TestClient(app) as client:
        health = client.get("/api/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"

        normal = client.post("/api/events/generate", json={"mode": "normal", "user_id": "USR-102"})
        assert normal.status_code == 200
        assert normal.json()["generated"] >= 1

        suspicious = client.post("/api/events/generate", json={"mode": "suspicious", "user_id": "USR-102"})
        assert suspicious.status_code == 200
        result = suspicious.json()["results"][0]
        assert result["anomaly"]["is_anomaly"] is True
        assert result["risk"]["risk_score"] >= 60
        assert result["insight"]["summary"]
        assert result["decision"]["decision"] in {"FLAG", "BLOCK", "MONITOR"}

        events = client.get("/api/events")
        assert events.status_code == 200
        assert isinstance(events.json(), list)
