"""Povezava na relacijsko bazo (MySQL) prek SQLAlchemy."""
from __future__ import annotations

import logging
import time

from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: seja na zahtevek."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(retries: int = 20, delay: float = 3.0) -> None:
    """Počaka, da je MySQL na voljo, in ustvari tabele."""
    from . import models  # noqa: F401  (registracija modelov)

    last_err: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            with engine.connect() as conn:  # preveri povezavo
                conn.exec_driver_sql("SELECT 1")
            Base.metadata.create_all(bind=engine)
            logger.info("Relacijska baza je pripravljena (tabele ustvarjene).")
            return
        except OperationalError as exc:
            last_err = exc
            logger.warning("MySQL še ni dosegljiv (poskus %s/%s) ...", attempt, retries)
            time.sleep(delay)
    raise RuntimeError(f"Povezava na MySQL ni uspela: {last_err}")
