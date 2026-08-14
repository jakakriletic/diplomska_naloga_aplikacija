"""Skupni SQL izrazi za konsistentne poizvedbe med endpointi."""
from __future__ import annotations

from sqlalchemy import case, func, select

from .models import Organization


def organization_domain_key():
    """Vrne normalizirano domeno iz URL-ja (brez sheme, poti in predpone www)."""
    without_scheme = func.substring_index(func.lower(Organization.source_url), "://", -1)
    host_with_port = func.substring_index(without_scheme, "/", 1)
    host = func.substring_index(host_with_port, ":", 1)
    return case(
        (host.like("www.%"), func.substring(host, 5)),
        else_=host,
    )


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
