"""Pydantic sheme za API odgovore in zahteve."""
from __future__ import annotations

import ipaddress
import socket
from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit, urlunsplit

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_SOURCE_URL_LENGTH = 512
DataScope = Literal["latest", "all"]


def validate_public_http_url(value: str | None) -> str | None:
    """Normalizira URL in zavrne lokalne oziroma zasebne omrežne cilje."""
    if value is None or not value.strip():
        return None

    value = value.strip()
    if len(value) > MAX_SOURCE_URL_LENGTH:
        raise ValueError(f"URL je lahko dolg največ {MAX_SOURCE_URL_LENGTH} znakov.")

    parsed = urlsplit(value)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Vnesi veljaven javni URL s protokolom http ali https.")
    if parsed.username or parsed.password:
        raise ValueError("URL ne sme vsebovati uporabniškega imena ali gesla.")

    host = parsed.hostname.lower().rstrip(".")
    if host == "localhost" or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("Lokalni in interni omrežni naslovi niso dovoljeni.")

    try:
        port = parsed.port
    except ValueError as exc:
        raise ValueError("URL vsebuje neveljavna vrata.") from exc

    try:
        addresses = {ipaddress.ip_address(host)}
    except ValueError:
        try:
            addresses = {
                ipaddress.ip_address(info[4][0])
                for info in socket.getaddrinfo(
                    host,
                    port or (443 if parsed.scheme.lower() == "https" else 80),
                    type=socket.SOCK_STREAM,
                )
            }
        except socket.gaierror as exc:
            raise ValueError("Domene ni bilo mogoče razrešiti.") from exc

    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Lokalni in zasebni omrežni naslovi niso dovoljeni.")

    normalized_host = f"[{host}]" if ":" in host else host
    netloc = f"{normalized_host}:{port}" if port else normalized_host
    return urlunsplit(
        (
            parsed.scheme.lower(),
            netloc,
            parsed.path or "/",
            parsed.query,
            "",
        )
    )


class RunRequest(BaseModel):
    """Zahteva za zagon pipelina. Brez URL-ja se uporabi privzeti vir (FEI)."""
    url: str | None = None

    @field_validator("url")
    @classmethod
    def validate_url(cls, value: str | None) -> str | None:
        return validate_public_http_url(value)


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
    question: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=6, ge=1, le=20)
    scope: DataScope = "latest"

    @field_validator("question")
    @classmethod
    def normalize_question(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Vprašanje je prazno.")
        return value


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
