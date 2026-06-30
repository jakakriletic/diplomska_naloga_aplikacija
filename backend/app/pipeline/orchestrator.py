"""ORKESTRATOR pipelina: poveže vse module v en proces.

Potek (skladno z arhitekturo iz diplome):
    1. ZAJEM        -> Scrapy strga spletni vir (web scraping)
    2. ČIŠČENJE     -> normalizacija besedila
    3. CHUNKING     -> razdelitev na smiselne enote
    4. AI EKSTRAKCIJA -> strukturiranje metapodatkov (OpenAI)
    5. RELACIJSKA BAZA -> shranjevanje strukturiranih podatkov (MySQL)
    6. VEKTORSKA BAZA  -> embeddingi chunkov (Qdrant)

Zagon teče v ozadju (nit), status in dnevnik se sproti zapisujeta v bazo,
da ju lahko frontend spremlja v realnem času.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import uuid
from datetime import datetime
from pathlib import Path

from ..config import settings
from ..db import SessionLocal
from ..models import Chunk, Organization, Page, PipelineRun
from . import chunking, cleaning, embedding, extraction
from .. import vector_store

logger = logging.getLogger(__name__)

# .../backend/scraper
SCRAPER_DIR = Path(__file__).resolve().parents[2] / "scraper"
SUBPROCESS_TIMEOUT = 600  # 10 minut
MIN_PAGE_CHARS = 50


# ---------------------------------------------------------------------------
#  Javni vmesnik
# ---------------------------------------------------------------------------
def start_run(url: str | None = None) -> str:
    """Ustvari zapis o zagonu in v ozadju zažene celoten pipeline."""
    run_id = str(uuid.uuid4())
    source_url = (url or settings.DEFAULT_START_URL).strip()

    db = SessionLocal()
    try:
        run = PipelineRun(id=run_id, status="pending", source_url=source_url)
        db.add(run)
        db.commit()
    finally:
        db.close()

    thread = threading.Thread(target=_execute_run, args=(run_id, source_url), daemon=True)
    thread.start()
    return run_id


# ---------------------------------------------------------------------------
#  Notranje
# ---------------------------------------------------------------------------
class _Logger:
    """Zbira dnevniške vrstice in jih sproti zapisuje v bazo."""

    def __init__(self, db, run: PipelineRun):
        self.db = db
        self.run = run
        self.lines: list[str] = []

    def log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{stamp}] {message}"
        self.lines.append(line)
        logger.info(message)
        self.run.log = "\n".join(self.lines)
        self.db.commit()


def _run_scrapy(run_id: str, url: str, log: _Logger) -> list[dict]:
    output_rel = f"output/run_{run_id}.json"
    output_abs = SCRAPER_DIR / output_rel
    output_abs.parent.mkdir(parents=True, exist_ok=True)
    if output_abs.exists():
        output_abs.unlink()

    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "fei",
        "-a", f"start_url={url}",
        "-a", f"max_depth={settings.SCRAPE_MAX_DEPTH}",
        "-s", f"CLOSESPIDER_PAGECOUNT={settings.SCRAPE_MAX_PAGES}",
        "-O", output_rel,
    ]
    log.log(f"Zaganjam zajem (scrapy): {url} (max {settings.SCRAPE_MAX_PAGES} strani, globina {settings.SCRAPE_MAX_DEPTH})")

    proc = subprocess.run(
        cmd,
        cwd=str(SCRAPER_DIR),
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )

    if not output_abs.exists():
        tail = (proc.stderr or "")[-800:]
        raise RuntimeError(f"Scrapy ni ustvaril izhoda. Napaka:\n{tail}")

    with open(output_abs, "r", encoding="utf-8") as f:
        data = json.load(f)

    try:
        output_abs.unlink()
    except OSError:
        pass

    return data if isinstance(data, list) else []


def _dedupe_pages(raw_pages: list[dict]) -> list[dict]:
    """Obdrži po en (najbogatejši) zapis na URL."""
    best: dict[str, dict] = {}
    for page in raw_pages:
        url = page.get("url")
        if not url:
            continue
        text = cleaning.clean(page.get("html", ""))
        if len(text) < MIN_PAGE_CHARS:
            continue
        page = {"url": url, "depth": page.get("depth", 0), "text": text}
        if url not in best or len(text) > len(best[url]["text"]):
            best[url] = page
    return list(best.values())


def _build_extraction_text(pages: list[dict]) -> str:
    """Združi besedilo strani; relevantnejše (manjša globina) najprej."""
    ordered = sorted(pages, key=lambda p: (p["depth"], -len(p["text"])))
    return "\n\n".join(p["text"] for p in ordered)


def _execute_run(run_id: str, url: str) -> None:
    db = SessionLocal()
    try:
        run = db.get(PipelineRun, run_id)
        if run is None:
            return
        run.status = "running"
        db.commit()
        log = _Logger(db, run)

        # --- 1. ZAJEM ---
        raw_pages = _run_scrapy(run_id, url, log)
        pages = _dedupe_pages(raw_pages)
        log.log(f"Zajetih in očiščenih strani: {len(pages)}")
        if not pages:
            raise RuntimeError("Zajem ni vrnil nobene uporabne strani.")

        # --- shranjevanje strani (relacijska baza) ---
        page_objs: list[Page] = []
        for p in pages:
            page = Page(
                run_id=run_id,
                url=p["url"][:512],
                depth=p["depth"],
                clean_text=p["text"],
                char_count=len(p["text"]),
            )
            db.add(page)
            page_objs.append(page)
        db.flush()  # dodeli ID-je strani

        # --- 4. AI EKSTRAKCIJA -> 5. RELACIJSKA BAZA ---
        org_name = None
        try:
            log.log(f"AI ekstrakcija metapodatkov (model: {settings.OPENAI_MODEL}) ...")
            extraction_text = _build_extraction_text(pages)
            org_data = extraction.extract_organization(extraction_text, url)
            org = Organization(run_id=run_id, **org_data)
            db.add(org)
            db.flush()
            org_name = org.name
            run.organizations_extracted = 1
            db.commit()
            log.log(f"Strukturirano: {org_name} (panoga: {org.industry or 'n/a'})")
        except Exception as exc:  # noqa: BLE001
            log.log(f"OPOZORILO: AI ekstrakcija ni uspela: {exc}")

        # --- 3. CHUNKING -> shranjevanje (relacijska baza) ---
        log.log("Razdeljevanje besedila na chunke ...")
        chunk_objs: list[Chunk] = []
        chunk_texts: list[str] = []
        for page in page_objs:
            for idx, ctext in enumerate(chunking.chunk_text(page.clean_text)):
                chunk = Chunk(
                    run_id=run_id,
                    page_id=page.id,
                    chunk_index=idx,
                    text=ctext,
                    char_count=len(ctext),
                    qdrant_point_id=vector_store.new_point_id(),
                )
                db.add(chunk)
                chunk_objs.append(chunk)
                chunk_texts.append(ctext)
        db.flush()  # dodeli ID-je chunkov
        run.chunks_created = len(chunk_objs)
        run.pages_scraped = len(page_objs)
        db.commit()
        log.log(f"Ustvarjenih chunkov: {len(chunk_objs)}")

        # --- 6. VEKTORSKA BAZA (embeddingi + Qdrant) ---
        if chunk_objs:
            try:
                log.log(f"Tvorba embeddingov (model: {settings.OPENAI_EMBEDDING_MODEL}) ...")
                vectors = embedding.embed_texts(chunk_texts)
                points = []
                for chunk, vector in zip(chunk_objs, vectors):
                    points.append({
                        "id": chunk.qdrant_point_id,
                        "vector": vector,
                        "payload": {
                            "chunk_id": chunk.id,
                            "page_id": chunk.page_id,
                            "url": next((p.url for p in page_objs if p.id == chunk.page_id), ""),
                            "organization": org_name,
                            "run_id": run_id,
                            "text": chunk.text[:1500],
                        },
                    })
                vector_store.upsert_chunks(points)
                log.log(f"Shranjenih vektorjev v Qdrant: {len(points)}")
            except Exception as exc:  # noqa: BLE001
                log.log(f"OPOZORILO: Vektorizacija ni uspela: {exc}")

        # --- zaključek ---
        run.status = "completed"
        run.finished_at = datetime.now()
        db.commit()
        log.log("Pipeline uspešno zaključen.")

    except Exception as exc:  # noqa: BLE001
        logger.exception("Napaka v pipelinu")
        try:
            run = db.get(PipelineRun, run_id)
            if run is not None:
                run.status = "failed"
                run.error = str(exc)[:2000]
                run.finished_at = datetime.now()
                if run.log:
                    run.log += f"\n[NAPAKA] {exc}"
                db.commit()
        except Exception:  # noqa: BLE001
            pass
    finally:
        db.close()
