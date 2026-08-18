"""Endpointi za pregled zajetih strani in njihovih chunkov."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Chunk, Page
from ..queries import latest_data_run_ids
from ..schemas import ChunkOut, DataScope, PageDetail, PageOut

router = APIRouter(prefix="/api/pages", tags=["pages"])


@router.get("", response_model=list[PageOut])
def list_pages(
    run_id: str | None = None,
    scope: DataScope = "latest",
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Page).order_by(Page.id.desc())
    if run_id:
        stmt = stmt.where(Page.run_id == run_id)
    elif scope == "latest":
        stmt = stmt.where(Page.run_id.in_(latest_data_run_ids()))
    stmt = stmt.offset(offset).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{page_id}", response_model=PageDetail)
def get_page(page_id: int, db: Session = Depends(get_db)):
    page = db.get(Page, page_id)
    if page is None:
        raise HTTPException(status_code=404, detail="Stran ni najdena.")
    return page


@router.get("/{page_id}/chunks", response_model=list[ChunkOut])
def get_page_chunks(page_id: int, db: Session = Depends(get_db)):
    if db.get(Page, page_id) is None:
        raise HTTPException(status_code=404, detail="Stran ni najdena.")
    stmt = select(Chunk).where(Chunk.page_id == page_id).order_by(Chunk.chunk_index)
    return list(db.scalars(stmt).all())
