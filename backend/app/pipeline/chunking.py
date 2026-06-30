"""Modul za RAZDELITEV besedila na smiselne enote (chunking).

Besedilo razbije na chunke določene velikosti z delnim prekrivanjem (overlap),
pri čemer spoštuje meje stavkov. Tako vsak chunk ostane vsebinsko zaokrožen,
prekrivanje pa ohrani kontekst med sosednjimi chunki za boljše semantično
iskanje.
"""
from __future__ import annotations

import re

from ..config import settings

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT.split(text)
    return [p.strip() for p in parts if p.strip()]


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[str]:
    chunk_size = chunk_size or settings.CHUNK_SIZE
    overlap = overlap if overlap is not None else settings.CHUNK_OVERLAP

    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= chunk_size:
        return [text]

    sentences = split_sentences(text)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        # Zelo dolg stavek razbijemo na trde kose
        if len(sentence) > chunk_size:
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(sentence), chunk_size):
                chunks.append(sentence[i : i + chunk_size].strip())
            continue

        if len(current) + len(sentence) + 1 <= chunk_size:
            current = f"{current} {sentence}".strip()
        else:
            chunks.append(current.strip())
            # prenesi rep prejšnjega chunka kot overlap
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail} {sentence}".strip()

    if current.strip():
        chunks.append(current.strip())

    return [c for c in chunks if c]
