"""Endpointi za iskanje: semantično (Qdrant) in po ključnih besedah (MySQL)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Chunk, Page
from ..pipeline import embedding
from ..schemas import KeywordHit, SemanticHit
from .. import vector_store

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("/semantic", response_model=list[SemanticHit])
def semantic_search(
    q: str = Query(..., min_length=1),
    limit: int = 10,
):
    """Semantično iskanje po vektorski bazi (po vsebinski podobnosti)."""
    try:
        query_vector = embedding.embed_query(q)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"Embedding poizvedbe ni uspel (preveri OPENAI_API_KEY): {exc}",
        )
    try:
        hits = vector_store.search(query_vector, limit=limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Iskanje v Qdrant ni uspelo: {exc}")
    return hits


@router.get("/keyword", response_model=list[KeywordHit])
def keyword_search(
    q: str = Query(..., min_length=1),
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """Klasično iskanje po ključnih besedah po besedilu chunkov (relacijska baza)."""
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
