from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class EventIn(BaseModel):
    event_id: Optional[str] = None
    user_id: str
    source: str = "transaction"
    event_type: str = "payment"
    transaction_amount: float = Field(..., ge=0)
    currency: str = "INR"
    device_id: str = "DEV-UNKNOWN"
    location: str = "Unknown"
    beneficiary: str = "UNKNOWN"
    timestamp: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GenerateRequest(BaseModel):
    mode: str = Field(pattern="^(normal|suspicious|burst)$")
    user_id: str = "USR-102"
    count: int = 1


class ActionExecuteRequest(BaseModel):
    action_type: Optional[str] = None


class EventOut(BaseModel):
    event_id: str
    user_id: str
    source: str
    transaction_amount: Optional[float] = None
    anomaly: bool = False
    risk_score: int = 0
    severity: str = "LOW"
    decision: str = "ALLOW"
    status: str = "received"
