from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.api import router
from backend.config import FRONTEND_ORIGIN
from backend.database.db import init_database, seed_database
from backend.ml.behavior import BehaviorAnalyzer
from backend.processing.pipeline import Pipeline
from backend.services.bus import EventBus

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()
    seed_database()
    analyzer = BehaviorAnalyzer()
    for user_id in ("USR-102", "USR-201", "USR-305", "USR-410"):
        analyzer.rebuild_profile(user_id)
    pipe = Pipeline()
    bus = EventBus()

    async def publish(event_type: str, payload: dict):
        await bus.publish(event_type, payload)

    pipe.publish = publish
    app.state.pipeline = pipe
    app.state.bus = bus
    yield


app = FastAPI(
    title="RevoralQ API",
    description="Real-Time AI Monitoring & Intelligence",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173", "http://localhost:8000", "http://127.0.0.1:8000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")
app.include_router(router)


@app.get("/docs-info")
def docs_info():
    return {"openapi": "/openapi.json", "swagger": "/docs"}


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{full_path:path}")
    async def spa(full_path: str):
        index = FRONTEND_DIST / "index.html"
        file_path = FRONTEND_DIST / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(index)
