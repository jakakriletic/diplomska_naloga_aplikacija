"""Endpointi za pregled strukturiranih podatkov o organizacijah (MySQL)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Organization
from ..queries import latest_organization_versions
from ..schemas import OrganizationOut

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_organizations(
    q: str | None = Query(None, max_length=500),
    limit: int = Query(100, ge=1, le=500),
    include_history: bool = False,
    db: Session = Depends(get_db),
):
    """Seznam zadnjih različic organizacij; po želji tudi celotna zgodovina."""
    if include_history:
        stmt = select(Organization)
    else:
        ranked_versions = latest_organization_versions()
        stmt = (
            select(Organization)
            .join(
                ranked_versions,
                ranked_versions.c.organization_id == Organization.id,
            )
            .where(ranked_versions.c.version_rank == 1)
        )

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
