"""Centralna konfiguracija aplikacije, prebrana iz okoljskih spremenljivk."""
from __future__ import annotations

import os
from functools import lru_cache


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


class Settings:
    # --- MySQL (relacijska baza) ---
    MYSQL_HOST: str = os.getenv("MYSQL_HOST", "mysql")
    MYSQL_PORT: int = _int("MYSQL_PORT", 3306)
    MYSQL_USER: str = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD: str = os.getenv("MYSQL_PASSWORD", "rootpass")
    MYSQL_DATABASE: str = os.getenv("MYSQL_DATABASE", "companiesdb")

    # --- Qdrant (vektorska baza) ---
    QDRANT_URL: str = os.getenv("QDRANT_URL", "http://qdrant:6333")
    QDRANT_COLLECTION: str = os.getenv("QDRANT_COLLECTION", "company_chunks")

    # --- OpenAI ---
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_EMBEDDING_MODEL: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    EMBEDDING_DIM: int = _int("EMBEDDING_DIM", 1536)

    # --- Pipeline ---
    SCRAPE_MAX_PAGES: int = _int("SCRAPE_MAX_PAGES", 40)
    SCRAPE_MAX_DEPTH: int = _int("SCRAPE_MAX_DEPTH", 2)
    CHUNK_SIZE: int = _int("CHUNK_SIZE", 1200)
    CHUNK_OVERLAP: int = _int("CHUNK_OVERLAP", 150)

    # Privzeti vir za testni zajem (FEI UNM)
    DEFAULT_START_URL: str = os.getenv("DEFAULT_START_URL", "https://fei.uni-nm.si/")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}?charset=utf8mb4"
        )

    @property
    def openai_enabled(self) -> bool:
        return bool(self.OPENAI_API_KEY and self.OPENAI_API_KEY.strip())


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
