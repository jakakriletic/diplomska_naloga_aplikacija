"""Endpointi za pregled strukturiranih podatkov o organizacijah (MySQL)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Organization
from ..schemas import OrganizationOut

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.get("", response_model=list[OrganizationOut])
def list_organizations(q: str | None = None, limit: int = 100, db: Session = Depends(get_db)):
    """Seznam organizacij; z 'q' iskanje po imenu/panogi/dejavnosti/povzetku."""
    stmt = select(Organization).order_by(Organization.created_at.desc())
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
    stmt = stmt.limit(limit)
    return list(db.scalars(stmt).all())


@router.get("/{org_id}", response_model=OrganizationOut)
def get_organization(org_id: int, db: Session = Depends(get_db)):
    org = db.get(Organization, org_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organizacija ni najdena.")
    return org
