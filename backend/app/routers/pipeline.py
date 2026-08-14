"""Endpointi za upravljanje in spremljanje pipelina."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import PipelineRun
from ..pipeline import orchestrator
from ..schemas import RunDetail, RunRequest, RunSummary

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/run", response_model=RunSummary)
def run_pipeline(body: RunRequest, db: Session = Depends(get_db)):
    """Zažene celoten pipeline v ozadju in vrne zapis o zagonu."""
    try:
        run_id = orchestrator.start_run(body.url)
    except orchestrator.ActiveRunError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    run = db.get(PipelineRun, run_id)
    if run is None:
        raise HTTPException(status_code=500, detail="Zagona ni bilo mogoče ustvariti.")
    return run


@router.get("/runs", response_model=list[RunSummary])
def list_runs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    stmt = select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/latest", response_model=RunDetail | None)
def latest_run(db: Session = Depends(get_db)):
    stmt = select(PipelineRun).order_by(PipelineRun.started_at.desc()).limit(1)
    return db.scalars(stmt).first()


@router.get("/runs/{run_id}", response_model=RunDetail)
def get_run(run_id: str, db: Session = Depends(get_db)):
    run = db.get(PipelineRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Zagon ni najden.")
    return run
