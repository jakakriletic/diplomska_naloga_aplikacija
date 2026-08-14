"""Vstopna točka backenda (FastAPI).

Ob zagonu pripravi relacijsko bazo (MySQL) in vektorsko bazo (Qdrant),
nato izpostavi REST API za pipeline, organizacije, strani in iskanje.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from . import vector_store
from .config import settings
from .db import engine, init_db
from .pipeline import orchestrator
from .routers import chat, meta, organizations, pages, pipeline, search

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializacija relacijske baze (MySQL) ...")
    init_db()
    interrupted = orchestrator.mark_interrupted_runs()
    if interrupted:
        logger.warning("Kot prekinjenih označenih zagonov: %s", interrupted)
    legacy_updates = orchestrator.mark_legacy_warning_runs()
    if legacy_updates:
        logger.info("Uskladitev starejših opozorilnih zagonov, popravkov: %s", legacy_updates)
    logger.info("Inicializacija vektorske baze (Qdrant) ...")
    vector_store.ensure_collection()
    if not settings.openai_enabled:
        logger.warning("OPENAI_API_KEY ni nastavljen — AI ekstrakcija in embeddingi ne bodo delovali.")
    logger.info("Backend pripravljen.")
    yield


app = FastAPI(
    title="Zajem in strukturiranje podatkov o podjetjih",
    description="Diplomski prototip: scraping → čiščenje → chunking → AI → MySQL + Qdrant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pipeline.router)
app.include_router(organizations.router)
app.include_router(pages.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(meta.router)


@app.get("/api/health", tags=["meta"])
def health():
    checks: dict[str, str] = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        checks["mysql"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["mysql"] = "error"
        logger.warning("Healthcheck MySQL ni uspel: %s", exc)

    try:
        vector_store.get_client().get_collection(settings.QDRANT_COLLECTION)
        checks["qdrant"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["qdrant"] = "error"
        logger.warning("Healthcheck Qdrant ni uspel: %s", exc)

    if "error" in checks.values():
        raise HTTPException(status_code=503, detail={"status": "error", **checks})
    return {"status": "ok", **checks}
