"""Sloj za delo z vektorsko bazo (Qdrant).

Hrani embeddinge besedilnih chunkov in omogoča semantično iskanje.
Vsaka točka (point) ima payload z metapodatki, ki povezujejo vektor nazaj
na zapise v relacijski bazi (chunk_id, page_id, url, organization).
"""
from __future__ import annotations

import logging
import time
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from .config import settings

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None


def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(url=settings.QDRANT_URL, timeout=30.0)
    return _client


def ensure_collection(retries: int = 20, delay: float = 3.0) -> None:
    """Ustvari kolekcijo, če še ne obstaja (počaka, da je Qdrant na voljo)."""
    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            client = get_client()
            existing = {c.name for c in client.get_collections().collections}
            if settings.QDRANT_COLLECTION not in existing:
                client.create_collection(
                    collection_name=settings.QDRANT_COLLECTION,
                    vectors_config=qm.VectorParams(
                        size=settings.EMBEDDING_DIM,
                        distance=qm.Distance.COSINE,
                    ),
                )
                logger.info("Kolekcija '%s' ustvarjena.", settings.QDRANT_COLLECTION)
            else:
                logger.info("Kolekcija '%s' že obstaja.", settings.QDRANT_COLLECTION)
            return
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logger.warning("Qdrant še ni dosegljiv (poskus %s/%s) ...", attempt, retries)
            time.sleep(delay)
    raise RuntimeError(f"Povezava na Qdrant ni uspela: {last_err}")


def new_point_id() -> str:
    return str(uuid.uuid4())


def upsert_chunks(points: list[dict]) -> None:
    """Vstavi vektorje v Qdrant.

    Vsak element: {"id": str, "vector": list[float], "payload": dict}
    """
    if not points:
        return
    client = get_client()
    client.upsert(
        collection_name=settings.QDRANT_COLLECTION,
        points=[
            qm.PointStruct(id=p["id"], vector=p["vector"], payload=p["payload"])
            for p in points
        ],
    )


def _run_filter(run_ids: list[str] | None) -> qm.Filter | None:
    if run_ids is None:
        return None
    return qm.Filter(
        must=[
            qm.FieldCondition(
                key="run_id",
                match=qm.MatchAny(any=run_ids),
            )
        ]
    )


def search(
    query_vector: list[float],
    limit: int = 10,
    run_ids: list[str] | None = None,
) -> list[dict]:
    """Semantično iskanje: vrne najbolj podobne chunke s podobnostjo (score)."""
    client = get_client()
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=_run_filter(run_ids),
        limit=limit,
        with_payload=True,
    )
    hits: list[dict] = []
    for r in results:
        payload = r.payload or {}
        hits.append(
            {
                "score": float(r.score),
                "text": payload.get("text", ""),
                "url": payload.get("url", ""),
                "organization": payload.get("organization"),
                "chunk_id": payload.get("chunk_id"),
                "page_id": payload.get("page_id"),
            }
        )
    return hits


def count_vectors(run_ids: list[str] | None = None) -> int:
    if run_ids == []:
        return 0
    try:
        client = get_client()
        return int(
            client.count(
                settings.QDRANT_COLLECTION,
                count_filter=_run_filter(run_ids),
                exact=True,
            ).count
        )
    except Exception:  # noqa: BLE001
        return 0
