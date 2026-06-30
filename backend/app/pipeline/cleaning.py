"""Modul za ČIŠČENJE in NORMALIZACIJO besedila.

Surovo HTML čiščenje opravi že Scrapy pipeline. Tu izvedemo končno
normalizacijo besedila: poenotenje presledkov, odstranjevanje podvojenih
zaporednih odsekov in obrez praznih vrednosti.
"""
from __future__ import annotations

import re

_WS = re.compile(r"\s+")


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    # Poenoti presledke in nove vrstice
    text = _WS.sub(" ", text).strip()
    return text


def dedupe_segments(text: str, min_len: int = 40) -> str:
    """Odstrani podvojene daljše segmente (npr. ponavljajoče se menijske vrstice)."""
    if not text:
        return ""
    seen: set[str] = set()
    out: list[str] = []
    for segment in re.split(r"(?<=[.!?])\s+", text):
        key = segment.strip().lower()
        if len(key) >= min_len:
            if key in seen:
                continue
            seen.add(key)
        out.append(segment.strip())
    return " ".join(s for s in out if s)


def clean(text: str | None) -> str:
    return dedupe_segments(normalize_text(text))
