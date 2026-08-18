"""Skupni SQL izrazi za konsistentne poizvedbe med endpointi."""
from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from .models import Organization, PipelineRun

DATA_RUN_STATUSES = ("completed", "partial")


def _domain_key(url_column):
    """Normalizira domeno poljubnega stolpca URL (brez sheme, poti, vrat in www)."""
    without_scheme = func.substring_index(func.lower(url_column), "://", -1)
    host_with_port = func.substring_index(without_scheme, "/", 1)
    host = func.substring_index(host_with_port, ":", 1)
    return case(
        (host.like("www.%"), func.substring(host, 5)),
        else_=host,
    )


def organization_domain_key():
    """Vrne normalizirano domeno iz URL-ja (brez sheme, poti in predpone www)."""
    return _domain_key(Organization.source_url)


def pipeline_run_domain_key():
    """Vrne normalizirano domeno začetnega URL-ja zagona."""
    return _domain_key(PipelineRun.source_url)


def latest_data_run_versions():
    """Rangira zadnje uporabne zagone z zajetimi podatki znotraj vsake domene."""
    return (
        select(
            PipelineRun.id.label("run_id"),
            func.row_number()
            .over(
                partition_by=pipeline_run_domain_key(),
                order_by=(PipelineRun.started_at.desc(), PipelineRun.id.desc()),
            )
            .label("version_rank"),
        )
        .where(
            PipelineRun.status.in_(DATA_RUN_STATUSES),
            PipelineRun.pages_scraped > 0,
        )
        .subquery()
    )


def latest_data_run_ids():
    """SQL SELECT identifikatorjev zadnjega uporabnega zagona vsake domene."""
    ranked_runs = latest_data_run_versions()
    return select(ranked_runs.c.run_id).where(ranked_runs.c.version_rank == 1)


def get_latest_data_run_ids(db: Session) -> list[str]:
    """Vrne identifikatorje za filtriranje zunanje vektorske baze."""
    return list(db.scalars(latest_data_run_ids()).all())


def latest_organization_versions():
    """Podpoizvedba z rangom zapisov, kjer je 1 najnovejši zapis domene."""
    return (
        select(
            Organization.id.label("organization_id"),
            func.row_number()
            .over(
                partition_by=organization_domain_key(),
                order_by=(Organization.created_at.desc(), Organization.id.desc()),
            )
            .label("version_rank"),
        )
        .subquery()
    )
