"""Endpointi za iskanje: semantično (Qdrant) in po ključnih besedah (MySQL)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import vector_store
from ..db import get_db
from ..models import Chunk, Page
from ..pipeline import embedding
from ..schemas import KeywordHit, SemanticHit

router = APIRouter(prefix="/api/search", tags=["search"])
logger = logging.getLogger(__name__)


@router.get("/semantic", response_model=list[SemanticHit])
def semantic_search(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(10, ge=1, le=50),
):
    """Semantično iskanje po vektorski bazi (po vsebinski podobnosti)."""
    q = q.strip()
    if not q:
        raise HTTPException(status_code=422, detail="Iskalni niz je prazen.")
    try:
        query_vector = embedding.embed_query(q)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding iskalne poizvedbe ni uspel: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Semantično iskanje trenutno ni na voljo. Preveri OpenAI kvoto in nastavitve.",
        ) from exc
    try:
        hits = vector_store.search(query_vector, limit=limit)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Iskanje v Qdrant ni uspelo: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Vektorsko iskanje trenutno ni na voljo.",
        ) from exc
    return hits


@router.get("/keyword", response_model=list[KeywordHit])
def keyword_search(
    q: str = Query(..., min_length=1, max_length=500),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Klasično iskanje po ključnih besedah po besedilu chunkov (relacijska baza)."""
    q = q.strip()
    if not q:
        raise HTTPException(status_code=422, detail="Iskalni niz je prazen.")
    like = f"%{q}%"
    stmt = (
        select(Chunk, Page.url)
        .join(Page, Chunk.page_id == Page.id)
        .where(Chunk.text.like(like))
        .limit(limit)
    )
    results = db.execute(stmt).all()
    return [
        KeywordHit(chunk_id=chunk.id, page_id=chunk.page_id, url=url, text=chunk.text)
        for chunk, url in results
    ]
