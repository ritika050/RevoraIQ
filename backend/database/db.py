from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from backend.config import DB_PATH, DATA_DIR

SCHEMA_PATH = Path(__file__).with_name("schema.sql")


def utcnow() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def get_connection() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db_session():
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database() -> None:
    schema = SCHEMA_PATH.read_text(encoding="utf-8")
    with db_session() as conn:
        conn.executescript(schema)


def seed_database() -> None:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    users = [
        ("USR-102", "Ananya Rao", "ananya.rao@example.com", "Mumbai", "active"),
        ("USR-201", "Vikram Shah", "vikram.shah@example.com", "Bengaluru", "active"),
        ("USR-305", "Priya Nair", "priya.nair@example.com", "Delhi", "active"),
        ("USR-410", "Rahul Mehta", "rahul.mehta@example.com", "Pune", "active"),
    ]

    with db_session() as conn:
        existing = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"]
        if existing:
            return

        for user_id, name, email, city, status in users:
            conn.execute(
                """
                INSERT INTO users (user_id, name, email, city, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, name, email, city, status, utcnow()),
            )

        historical = [
            ("USR-102", [500, 800, 1200, 700, 950, 1100, 650], "DEV-12", "Mumbai", "BEN-01"),
            ("USR-201", [2200, 1800, 2500, 2100, 1900], "DEV-44", "Bengaluru", "BEN-22"),
            ("USR-305", [400, 550, 480, 620, 510], "DEV-08", "Delhi", "BEN-07"),
            ("USR-410", [1500, 1700, 1400, 1600], "DEV-31", "Pune", "BEN-15"),
        ]

        event_n = 10001
        for user_id, amounts, device, location, beneficiary in historical:
            for i, amount in enumerate(amounts):
                ts = (now - timedelta(hours=36 - i * 4)).replace(microsecond=0).isoformat()
                event_id = f"EVT-{event_n}"
                event_n += 1
                payload = {
                    "event_id": event_id,
                    "user_id": user_id,
                    "source": "transaction",
                    "event_type": "payment",
                    "transaction_amount": amount,
                    "currency": "INR",
                    "device_id": device,
                    "location": location,
                    "beneficiary": beneficiary if i % 3 else f"{beneficiary}",
                    "timestamp": ts,
                }
                conn.execute(
                    """
                    INSERT INTO events (
                        event_id, user_id, source, event_type, transaction_amount, currency,
                        device_id, location, beneficiary, payload_json, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_id,
                        user_id,
                        "transaction",
                        "payment",
                        amount,
                        "INR",
                        device,
                        location,
                        beneficiary,
                        json.dumps(payload),
                        "processed",
                        ts,
                    ),
                )

        conn.execute(
            """
            INSERT INTO audit_logs (event_id, actor, action, details, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (None, "system", "seed_database", "Loaded demo users and historical transactions", utcnow()),
        )
