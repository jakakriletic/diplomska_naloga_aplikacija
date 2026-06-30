"""Skupni OpenAI klient (uporabljata ga AI ekstrakcija in embeddingi)."""
from __future__ import annotations

from openai import OpenAI

from .config import settings

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_enabled:
            raise RuntimeError(
                "OPENAI_API_KEY ni nastavljen. Vpiši ga v .env datoteko."
            )
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client
