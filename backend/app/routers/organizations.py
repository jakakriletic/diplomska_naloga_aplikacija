"""Endpointi za pregled strukturiranih podatkov o organizacijah (MySQL)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Organization
from ..queries import latest_data_run_ids
from ..schemas import DataScope, OrganizationOut

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_organizations(
    q: str | None = Query(None, max_length=500),
    limit: int = Query(100, ge=1, le=500),
    scope: DataScope = "latest",
    include_history: bool | None = None,
    db: Session = Depends(get_db),
):
    """Seznam organizacij iz zadnjih uporabnih zagonov ali celotne zgodovine."""
    if include_history is not None:
        scope = "all" if include_history else "latest"

    stmt = select(Organization)
    if scope == "latest":
        stmt = stmt.where(Organization.run_id.in_(latest_data_run_ids()))

    q = q.strip() if q else None
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(
                Organization.name.like(like),
                Organization.industry.like(like),
                Organization.main_activity.like(like),
                Organization.summary.like(like),
                Organization.ceo.like(like),
            )
        )
    stmt = stmt.order_by(Organization.created_at.desc(), Organization.id.desc()).limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organizacija ni najdena.")
    return org
