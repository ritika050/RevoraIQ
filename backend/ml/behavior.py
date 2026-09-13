from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.database.db import db_session


class BehaviorAnalyzer:
    def get_profile(self, user_id: str) -> dict[str, Any]:
        with db_session() as conn:
            row = conn.execute(
                "SELECT * FROM behavior_profiles WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            if row:
                return self._row_to_profile(row)
            computed = self.rebuild_profile(user_id)
            return computed

    def rebuild_profile(self, user_id: str) -> dict[str, Any]:
        with db_session() as conn:
            rows = conn.execute(
                """
                SELECT transaction_amount, device_id, location, beneficiary, created_at
                FROM events
                WHERE user_id = ? AND status = 'processed'
                ORDER BY created_at ASC
                """,
                (user_id,),
            ).fetchall()

        amounts = [float(r["transaction_amount"] or 0) for r in rows]
        devices = sorted({r["device_id"] for r in rows if r["device_id"]})
        locations = sorted({r["location"] for r in rows if r["location"]})
        beneficiaries = sorted({r["beneficiary"] for r in rows if r["beneficiary"]})
        hours = sorted(
            {
                datetime.fromisoformat(r["created_at"].replace("Z", "+00:00")).hour
                for r in rows
                if r["created_at"]
            }
        )

        avg_amount = sum(amounts) / len(amounts) if amounts else 0
        profile = {
            "user_id": user_id,
            "avg_amount": round(avg_amount, 2),
            "min_amount": round(min(amounts), 2) if amounts else 0,
            "max_amount": round(max(amounts), 2) if amounts else 0,
            "txn_count": len(amounts),
            "frequency_per_hour": round(len(amounts) / max(1, len(hours) or 1), 2),
            "known_devices": devices,
            "known_locations": locations,
            "known_beneficiaries": beneficiaries,
            "typical_hours": hours or list(range(9, 19)),
            "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        }
        self._persist(profile)
        return profile

    def compare(self, event: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
        amount = float(event["transaction_amount"])
        avg = float(profile.get("avg_amount") or 0)
        deviation = round(amount / avg, 1) if avg else 0
        return {
            "normal_range": f"₹{int(profile.get('min_amount') or 0):,} - ₹{int(profile.get('max_amount') or 0):,}",
            "current": f"₹{int(amount):,}",
            "average": f"₹{int(avg):,}",
            "deviation": f"{deviation}x higher" if deviation >= 1 else f"{deviation}x",
            "deviation_value": deviation,
            "known_devices": profile.get("known_devices") or [],
            "known_locations": profile.get("known_locations") or [],
            "known_beneficiaries": profile.get("known_beneficiaries") or [],
        }

    def _persist(self, profile: dict[str, Any]) -> None:
        with db_session() as conn:
            conn.execute(
                """
                INSERT INTO behavior_profiles (
                    user_id, avg_amount, min_amount, max_amount, txn_count, frequency_per_hour,
                    known_devices, known_locations, known_beneficiaries, typical_hours, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    avg_amount=excluded.avg_amount,
                    min_amount=excluded.min_amount,
                    max_amount=excluded.max_amount,
                    txn_count=excluded.txn_count,
                    frequency_per_hour=excluded.frequency_per_hour,
                    known_devices=excluded.known_devices,
                    known_locations=excluded.known_locations,
                    known_beneficiaries=excluded.known_beneficiaries,
                    typical_hours=excluded.typical_hours,
                    updated_at=excluded.updated_at
                """,
                (
                    profile["user_id"],
                    profile["avg_amount"],
                    profile["min_amount"],
                    profile["max_amount"],
                    profile["txn_count"],
                    profile["frequency_per_hour"],
                    json.dumps(profile["known_devices"]),
                    json.dumps(profile["known_locations"]),
                    json.dumps(profile["known_beneficiaries"]),
                    json.dumps(profile["typical_hours"]),
                    profile["updated_at"],
                ),
            )

    def _row_to_profile(self, row) -> dict[str, Any]:
        return {
            "user_id": row["user_id"],
            "avg_amount": row["avg_amount"],
            "min_amount": row["min_amount"],
            "max_amount": row["max_amount"],
            "txn_count": row["txn_count"],
            "frequency_per_hour": row["frequency_per_hour"],
            "known_devices": json.loads(row["known_devices"] or "[]"),
            "known_locations": json.loads(row["known_locations"] or "[]"),
            "known_beneficiaries": json.loads(row["known_beneficiaries"] or "[]"),
            "typical_hours": json.loads(row["typical_hours"] or "[]"),
            "updated_at": row["updated_at"],
        }
