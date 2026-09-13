from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

from backend.api import queries
from backend.models.schemas import ActionExecuteRequest, EventIn, GenerateRequest
from backend.services.event_generator import (
    demo_sequence,
    generate_burst_events,
    generate_normal_event,
    generate_suspicious_event,
)

router = APIRouter()


def pipeline(request: Request):
    return request.app.state.pipeline


def bus(request: Request):
    return request.app.state.bus


@router.get("/health")
async def health(request: Request):
    return {"status": "ok", **queries.system_status(pipeline(request))}


@router.get("/metrics")
async def metrics():
    return queries.metrics()


@router.get("/events")
async def get_events(
    event_id: str | None = None,
    user_id: str | None = None,
    event_type: str | None = None,
    source: str | None = None,
    severity: str | None = None,
    anomaly: str | None = None,
    date: str | None = None,
):
    return queries.list_events(
        {
            "event_id": event_id,
            "user_id": user_id,
            "event_type": event_type,
            "source": source,
            "severity": severity,
            "anomaly": anomaly,
            "date": date,
        }
    )


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    detail = queries.get_event_detail(event_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Event not found")
    return detail


@router.post("/events")
async def post_event(payload: EventIn, request: Request):
    return await pipeline(request).ingest(payload.model_dump())


@router.post("/events/generate")
async def generate_events(body: GenerateRequest, request: Request):
    pipe = pipeline(request)
    results = []
    if body.mode == "normal":
        results.append(await pipe.ingest(generate_normal_event(body.user_id)))
    elif body.mode == "suspicious":
        results.append(await pipe.ingest(generate_suspicious_event(body.user_id)))
    else:
        for event in generate_burst_events(body.user_id, max(2, body.count)):
            results.append(await pipe.ingest(event))
    return {"generated": len(results), "results": results}


@router.post("/demo/run")
async def run_demo(request: Request):
    pipe = pipeline(request)
    if pipe.demo_running:
        return {"status": "already_running"}
    asyncio.create_task(_run_demo(pipe, paced=True))
    return {"status": "started"}


@router.post("/demo/scenario")
async def run_scenario(request: Request):
    pipe = pipeline(request)
    if pipe.demo_running:
        return {"status": "already_running"}
    asyncio.create_task(_run_demo(pipe, paced=False))
    return {"status": "started"}


async def _run_demo(pipe, paced: bool = True) -> None:
    pipe.demo_running = True
    gap = 11.0 if paced else 1.2
    try:
        await pipe.emit("demo", {"message": "Demo mode started — establishing a normal baseline for USR-102", "step": 0})
        if paced:
            await asyncio.sleep(4)
        sequence = demo_sequence("USR-102")
        for i, event in enumerate(sequence, start=1):
            is_last = i == len(sequence)
            await pipe.emit(
                "demo",
                {
                    "message": (
                        "Suspicious ₹75,000 spike from a new device and new beneficiary"
                        if is_last
                        else f"Ingesting normal ₹{int(event['transaction_amount']):,} payment for USR-102"
                    ),
                    "step": i,
                    "total": len(sequence),
                },
            )
            await pipe.ingest(event, auto_action_critical=is_last)
            await asyncio.sleep(gap if not is_last else (6 if paced else 0.8))
        await pipe.emit("demo", {"message": "Demo complete — alert raised and recommended action executed", "step": len(sequence), "done": True})
    finally:
        pipe.demo_running = False


@router.get("/alerts")
async def get_alerts(status: str | None = Query(default=None)):
    return queries.list_alerts(status)


@router.post("/alerts/{event_id}/dismiss")
async def dismiss_alert(event_id: str):
    from backend.database.db import db_session, utcnow

    with db_session() as conn:
        conn.execute("UPDATE alerts SET status = 'dismissed' WHERE event_id = ?", (event_id,))
        conn.execute(
            "INSERT INTO audit_logs (event_id, actor, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (event_id, "operator", "dismiss_alert", "Alert dismissed from dashboard", utcnow()),
        )
    return {"status": "dismissed", "event_id": event_id}


@router.get("/users/{user_id}/profile")
async def user_profile(user_id: str, request: Request):
    return pipeline(request).behavior.get_profile(user_id)


@router.get("/insights/{event_id}")
async def insights(event_id: str):
    detail = queries.get_event_detail(event_id)
    if not detail or not detail.get("insight"):
        raise HTTPException(status_code=404, detail="Insight not found")
    return detail["insight"]


@router.post("/actions/{event_id}/execute")
async def execute_action(event_id: str, body: ActionExecuteRequest, request: Request):
    detail = queries.get_event_detail(event_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Event not found")
    decision = detail.get("decision") or {}
    action_type = body.action_type or decision.get("decision")
    mapping = {
        "BLOCK": "BLOCK_TRANSACTION",
        "FLAG": "FLAG_AND_ALERT",
        "MONITOR": "MONITOR",
        "ALLOW": "ALLOW",
        "BLOCK_TRANSACTION": "BLOCK_TRANSACTION",
        "FLAG_AND_ALERT": "FLAG_AND_ALERT",
        "CREATE_INCIDENT": "CREATE_INCIDENT",
    }
    resolved = mapping.get(action_type, "CREATE_INCIDENT")
    reason = (decision or {}).get("rationale") or "Operator executed recommended action"
    result = pipeline(request).actions.execute(event_id, resolved, reason)
    await pipeline(request).emit("action", result)
    await pipeline(request).emit("pipeline", {"stage": "action", "message": "Action triggered...", "event_id": event_id})
    return result


@router.get("/audit-logs")
async def get_audit_logs():
    return queries.audit_logs()


@router.get("/admin/status")
async def admin_status(request: Request):
    return queries.system_status(pipeline(request))


@router.get("/stream")
async def stream(request: Request):
    event_bus = bus(request)

    async def event_generator():
        queue = await event_bus.subscribe()
        try:
            yield "event: ready\ndata: {\"status\":\"connected\"}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=15)
                    payload = json.loads(message)
                    yield f"event: {payload['type']}\ndata: {json.dumps(payload['payload'])}\n\n"
                except asyncio.TimeoutError:
                    yield "event: ping\ndata: {}\n\n"
        finally:
            await event_bus.unsubscribe(queue)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
