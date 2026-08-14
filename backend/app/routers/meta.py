"""Pomožni endpointi: statistika za nadzorno ploščo."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import vector_store
from ..db import get_db
from ..models import Chunk, Page, PipelineRun
from ..queries import organization_domain_key
from ..schemas import RunSummary, Stats

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/stats", response_model=Stats)
def get_stats(db: Session = Depends(get_db)):
    runs = db.scalar(select(func.count(PipelineRun.id))) or 0
    organizations = db.scalar(
        select(func.count(func.distinct(organization_domain_key())))
    ) or 0
    pages = db.scalar(select(func.count(Page.id))) or 0
    chunks = db.scalar(select(func.count(Chunk.id))) or 0
    last_run = db.scalars(
        select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
    ).first()
    return Stats(
        runs=runs,
        organizations=organizations,
        pages=pages,
        chunks=chunks,
        vectors=vector_store.count_vectors(),
        last_run=RunSummary.model_validate(last_run) if last_run else None,
    )
