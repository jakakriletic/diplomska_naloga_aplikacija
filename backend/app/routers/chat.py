"""Endpoint za AI KLEPET (RAG) nad zajetimi podatki — bonus funkcija.

Poveže semantično iskanje (pridobivanje koščkov) z generativnim modelom
(sestavljanje odgovora). Glej `app/pipeline/chat.py`.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import vector_store
from ..db import get_db
from ..pipeline import chat, embedding
from ..queries import get_latest_data_run_ids
from ..schemas import ChatRequest, ChatResponse, ChatSource

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ChatResponse)
def ask(body: ChatRequest, db: Session = Depends(get_db)):
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Vprašanje je prazno.")

    run_ids = get_latest_data_run_ids(db) if body.scope == "latest" else None
    if body.scope == "latest" and not run_ids:
        return ChatResponse(
            answer=(
                "V bazi ni zadnjih uspešno zajetih podatkov, na podlagi katerih bi lahko odgovoril. "
                "Najprej zaženi zajem na Nadzorni plošči."
            ),
            sources=[],
        )

    # 1. PRIDOBIVANJE (retrieval): vprašanje -> embedding -> najbolj podobni koščki
    try:
        query_vector = embedding.embed_query(question)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Embedding vprašanja za klepet ni uspel: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI klepet trenutno ni na voljo. Preveri OpenAI kvoto in nastavitve.",
        ) from exc
    try:
        hits = vector_store.search(query_vector, limit=body.limit, run_ids=run_ids)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Iskanje konteksta v Qdrant ni uspelo: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="Virov za odgovor trenutno ni mogoče poiskati.",
        ) from exc

    if not hits:
        return ChatResponse(
            answer=(
                "V bazi ni zajetih podatkov, na podlagi katerih bi lahko odgovoril. "
                "Najprej zaženi zajem na Nadzorni plošči."
            ),
            sources=[],
        )

    # 2. GENERIRANJE (generation): LLM sestavi odgovor na podlagi koščkov
    try:
        answer = chat.generate_answer(question, hits)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Generiranje odgovora ni uspelo: %s", exc)
        raise HTTPException(
            status_code=503,
            detail="AI odgovora trenutno ni mogoče ustvariti.",
        ) from exc

    sources = [
        ChatSource(
            url=h.get("url", ""),
            organization=h.get("organization"),
            text=h.get("text", ""),
            score=float(h.get("score", 0.0)),
        )
        for h in hits
    ]
    return ChatResponse(answer=answer, sources=sources)
