"""Modul za TVORBO VEKTORSKIH PREDSTAVITEV besedila (embeddingi).

Besedilne chunke pretvori v vektorje z OpenAI embedding modelom. Vektorji se
nato shranijo v vektorsko bazo (Qdrant) za semantično iskanje.
"""
from __future__ import annotations

import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..openai_client import get_client

logger = logging.getLogger(__name__)

BATCH_SIZE = 64


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _embed_batch(texts: list[str]) -> list[list[float]]:
    client = get_client()
    response = client.embeddings.create(
        model=settings.OPENAI_EMBEDDING_MODEL,
        input=texts,
    )
    # OpenAI ohrani vrstni red vhodov
    return [item.embedding for item in response.data]


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Vrne embeddinge za seznam besedil (paketno)."""
    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        vectors.extend(_embed_batch(batch))
    return vectors


def embed_query(text: str) -> list[float]:
    """Vrne embedding za eno iskalno poizvedbo."""
    return _embed_batch([text])[0]
