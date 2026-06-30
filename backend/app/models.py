"""SQLAlchemy modeli (relacijska shema).

Shema je normalizirana v skladu z idejo diplome:
  - pipeline_runs  : en zagon celotnega procesa (zajem -> ... -> shranjevanje)
  - organizations  : strukturirani metapodatki o organizaciji/podjetju (izhod AI)
  - pages          : posamezne zajete in očiščene spletne strani
  - chunks         : besedilne enote (chunki) za semantično indeksiranje
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    source_url: Mapped[str] = mapped_column(String(512))
    pages_scraped: Mapped[int] = mapped_column(Integer, default=0)
    chunks_created: Mapped[int] = mapped_column(Integer, default=0)
    organizations_extracted: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    log: Mapped[str | None] = mapped_column(LONGTEXT, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    organizations: Mapped[list["Organization"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    pages: Mapped[list["Page"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="run", cascade="all, delete-orphan"
    )


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)

    name: Mapped[str] = mapped_column(String(255), index=True)
    source_url: Mapped[str] = mapped_column(String(512))
    ceo: Mapped[str | None] = mapped_column(String(255), nullable=True)
    founded_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    main_activity: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["PipelineRun"] = relationship(back_populates="organizations")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)

    # 512 znakov * 4 bajte (utf8mb4) = 2048 bajtov < 3072 (varna meja InnoDB indeksa)
    url: Mapped[str] = mapped_column(String(512), index=True)
    depth: Mapped[int] = mapped_column(Integer, default=0)
    clean_text: Mapped[str] = mapped_column(LONGTEXT)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["PipelineRun"] = relationship(back_populates="pages")
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="page", cascade="all, delete-orphan"
    )


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id"), index=True)
    page_id: Mapped[int] = mapped_column(ForeignKey("pages.id"), index=True)

    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    # ID točke v vektorski bazi (Qdrant) — povezava relacijska <-> vektorska baza
    qdrant_point_id: Mapped[str] = mapped_column(String(36), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    run: Mapped["PipelineRun"] = relationship(back_populates="chunks")
    page: Mapped["Page"] = relationship(back_populates="chunks")
