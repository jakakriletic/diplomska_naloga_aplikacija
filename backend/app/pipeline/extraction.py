"""Modul za EKSTRAKCIJO in STRUKTURIRANJE metapodatkov z generativno UI.

Iz (pogosto nestrukturiranega) besedila spletne strani z uporabo OpenAI modela
in promptnega inženirstva izlušči vnaprej določene metapodatke o organizaciji
in jih vrne v strukturirani (JSON) obliki, skladni z relacijsko shemo.
"""
from __future__ import annotations

import json
import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..openai_client import get_client

logger = logging.getLogger(__name__)

# Največ besedila, ki ga pošljemo modelu (varčevanje s tokeni)
MAX_INPUT_CHARS = 12000

SYSTEM_PROMPT = """\
Si pomočnik za ekstrakcijo informacij (information extraction).

Tvoja naloga je iz šumnega, nestrukturiranega besedila spletne strani neke
organizacije ali podjetja izluščiti SAMO relevantne strukturirane podatke.

Izlušči naslednja polja in jih vrni kot JSON objekt s točno temi ključi:
  - company_name (string): uradno ime organizacije/podjetja
  - ceo (string|null): direktor, dekan, predsednik ali glavna vodilna oseba
  - founded_year (integer|null): leto ustanovitve
  - industry (string|null): glavna panoga/področje (npr. izobraževanje, IT, energetika)
  - main_activity (string|null): kratek opis glavne dejavnosti
  - summary (string|null): kratek, jedrnat povzetek organizacije (2-3 stavki)
  - email (string|null): kontaktni e-poštni naslov, če obstaja
  - phone (string|null): kontaktna telefonska številka, če obstaja
  - address (string|null): naslov/sedež, če obstaja

Pravila:
  - Uporabi IZKLJUČNO podatke iz vhodnega besedila. Ne izmišljuj si vrednosti.
  - Če podatek ni jasno razviden, vrni null za to polje.
  - Za ceo vrni ime in priimek ene glavne vodilne osebe. Prednost imajo CEO ali
    predsednik uprave, pri fakulteti dekan, sicer direktor. Ne vračaj celotnega
    seznama uprave ali nadzornega sveta.
  - founded_year mora biti celo število (npr. 2009), sicer null.
  - main_activity in summary naj bosta kratka in dejstvena, brez marketinškega jezika.
  - Odgovori IZKLJUČNO z veljavnim JSON objektom, brez dodatnega besedila.
"""

_FIELDS = (
    "company_name", "ceo", "founded_year", "industry",
    "main_activity", "summary", "email", "phone", "address",
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _call_model(text: str) -> dict:
    client = get_client()
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    "Iz spodnjega besedila izlušči strukturirane podatke o "
                    "organizaciji.\n\nBESEDILO:\n" + text
                ),
            },
        ],
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


def _coerce_year(value) -> int | None:
    try:
        year = int(value)
        return year if 1500 <= year <= 2100 else None
    except (TypeError, ValueError):
        return None


def extract_organization(text: str, source_url: str) -> dict:
    """Vrne strukturiran slovar polj organizacije (skladen z modelom Organization)."""
    snippet = (text or "")[:MAX_INPUT_CHARS]
    data = _call_model(snippet)

    # Poenoti in počisti polja
    result = {field: data.get(field) for field in _FIELDS}
    result["founded_year"] = _coerce_year(result.get("founded_year"))

    name = (result.get("company_name") or "").strip()
    if not name:
        # Rezerva: ime iz domene
        from urllib.parse import urlparse

        name = urlparse(source_url).netloc or "Neznana organizacija"

    return {
        "name": name,
        "source_url": source_url,
        "ceo": result.get("ceo"),
        "founded_year": result.get("founded_year"),
        "industry": result.get("industry"),
        "main_activity": result.get("main_activity"),
        "summary": result.get("summary"),
        "email": result.get("email"),
        "phone": result.get("phone"),
        "address": result.get("address"),
    }
