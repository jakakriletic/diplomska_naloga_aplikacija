"""Pomožni endpointi: statistika za nadzorno ploščo."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import vector_store
from ..db import get_db
from ..models import Chunk, Organization, Page, PipelineRun
from ..queries import get_latest_data_run_ids, latest_data_run_ids
from ..schemas import DataScope, RunSummary, Stats

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/stats", response_model=Stats)
def get_stats(scope: DataScope = "latest", db: Session = Depends(get_db)):
    run_ids: list[str] | None = None
    run_filter = None
    if scope == "latest":
        run_filter = latest_data_run_ids()
        run_ids = get_latest_data_run_ids(db)

    run_stmt = select(func.count(PipelineRun.id))
    organization_stmt = select(func.count(Organization.id))
    page_stmt = select(func.count(Page.id))
    chunk_stmt = select(func.count(Chunk.id))
    if run_filter is not None:
        run_stmt = run_stmt.where(PipelineRun.id.in_(run_filter))
        organization_stmt = organization_stmt.where(Organization.run_id.in_(run_filter))
        page_stmt = page_stmt.where(Page.run_id.in_(run_filter))
        chunk_stmt = chunk_stmt.where(Chunk.run_id.in_(run_filter))

    runs = db.scalar(run_stmt) or 0
    organizations = db.scalar(organization_stmt) or 0
    pages = db.scalar(page_stmt) or 0
    chunks = db.scalar(chunk_stmt) or 0
    last_run = db.scalars(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
    ).first()
    return Stats(
        runs=runs,
        organizations=organizations,
        pages=pages,
        chunks=chunks,
        vectors=vector_store.count_vectors(run_ids=run_ids),
        last_run=RunSummary.model_validate(last_run) if last_run else None,
    )
