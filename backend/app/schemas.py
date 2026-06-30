"""Pydantic sheme za API odgovore in zahteve."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunRequest(BaseModel):
    """Zahteva za zagon pipelina. Brez URL-ja se uporabi privzeti vir (FEI)."""
    url: str | None = None


class RunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    status: str
    source_url: str
    pages_scraped: int
    chunks_created: int
    organizations_extracted: int
    error: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class RunDetail(RunSummary):
    log: str | None = None


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    name: str
    source_url: str
    ceo: str | None = None
    founded_year: int | None = None
    industry: str | None = None
    main_activity: str | None = None
    summary: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    created_at: datetime | None = None


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: str
    url: str
    depth: int
    char_count: int
    scraped_at: datetime | None = None


class PageDetail(PageOut):
    clean_text: str


class ChunkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    page_id: int
    chunk_index: int
    text: str
    char_count: int


class SemanticHit(BaseModel):
    score: float
    text: str
    url: str
    organization: str | None = None
    chunk_id: int | None = None
    page_id: int | None = None


class KeywordHit(BaseModel):
    chunk_id: int
    page_id: int
    url: str
    text: str


# --- AI klepet (RAG) — bonus funkcija ---
class ChatRequest(BaseModel):
    """Vprašanje uporabnika; limit = koliko koščkov uporabimo kot kontekst."""
    question: str
    limit: int = 6


class ChatSource(BaseModel):
    """Vir (košček), na katerem temelji odgovor."""
    url: str
    organization: str | None = None
    text: str
    score: float = 0.0


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource]


class Stats(BaseModel):
    runs: int
    organizations: int
    pages: int
    chunks: int
    vectors: int
    last_run: RunSummary | None = None
