"""Endpoint za AI KLEPET (RAG) nad zajetimi podatki — bonus funkcija.

Poveže semantično iskanje (pridobivanje koščkov) z generativnim modelom
(sestavljanje odgovora). Glej `app/pipeline/chat.py`.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..pipeline import chat, embedding
from ..schemas import ChatRequest, ChatResponse, ChatSource
from .. import vector_store

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
def ask(body: ChatRequest):
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Vprašanje je prazno.")

    # 1. PRIDOBIVANJE (retrieval): vprašanje -> embedding -> najbolj podobni koščki
    try:
        query_vector = embedding.embed_query(question)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=503,
            detail=f"Embedding poizvedbe ni uspel (preveri OPENAI_API_KEY): {exc}",
        )
    try:
        hits = vector_store.search(query_vector, limit=body.limit)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=503, detail=f"Iskanje v Qdrant ni uspelo: {exc}")

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
        raise HTTPException(status_code=503, detail=f"Generiranje odgovora ni uspelo: {exc}")

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
