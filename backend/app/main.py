"""Vstopna točka backenda (FastAPI).

Ob zagonu pripravi relacijsko bazo (MySQL) in vektorsko bazo (Qdrant),
nato izpostavi REST API za pipeline, organizacije, strani in iskanje.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .db import init_db
from .routers import chat, meta, organizations, pages, pipeline, search
from . import vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Inicializacija relacijske baze (MySQL) ...")
    init_db()
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
    allow_origins=["*"],
    allow_credentials=True,
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
    return {"status": "ok"}
