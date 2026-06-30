"""AI KLEPET (RAG) nad zajetimi podatki — bonus funkcija.

Vzorec RAG (Retrieval-Augmented Generation):
    1. vprašanje uporabnika -> embedding -> pridobi relevantne koščke iz
       vektorske baze (to opravi klicatelj prek semantičnega iskanja),
    2. LLM (OpenAI) na podlagi SAMO teh koščkov sestavi odgovor v naravnem
       jeziku in se sklicuje na vire.

Tako se generativni model uporabi za odgovarjanje, a ostane "prizemljen" v
dejansko zajetih podatkih (ne izmišljuje si).
"""
from __future__ import annotations

import logging

from tenacity import retry, stop_after_attempt, wait_exponential

from ..config import settings
from ..openai_client import get_client

logger = logging.getLogger(__name__)

# Največ besedila konteksta, ki ga pošljemo modelu (varčevanje s tokeni)
MAX_CONTEXT_CHARS = 9000

SYSTEM_PROMPT = """\
Si pomočnik, ki odgovarja na vprašanja o organizacijah in podjetjih IZKLJUČNO na
podlagi priloženih odlomkov besedila (kontekst), zajetih z njihovih spletnih strani.

Pravila:
  - Odgovori SAMO na podlagi konteksta. Ne uporabljaj zunanjega znanja in si ne izmišljuj.
  - Če v kontekstu ni dovolj informacij za odgovor, to jasno in iskreno povej.
  - Odgovori v jeziku vprašanja (privzeto slovenščina), tudi če je kontekst v drugem jeziku.
  - Bodi jedrnat in dejstven, brez marketinškega jezika.
  - Kjer je smiselno, se sklicuj na vir z oznako [1], [2] ... glede na oštevilčene odlomke.
"""


def _build_context(chunks: list[dict]) -> str:
    """Sestavi oštevilčen kontekst iz pridobljenih koščkov (z navedbo vira)."""
    parts: list[str] = []
    used = 0
    for i, c in enumerate(chunks, start=1):
        org = c.get("organization") or "neznana organizacija"
        url = c.get("url") or ""
        text = (c.get("text") or "").strip()
        block = f"[{i}] (vir: {org} — {url})\n{text}"
        if used + len(block) > MAX_CONTEXT_CHARS:
            break
        parts.append(block)
        used += len(block)
    return "\n\n".join(parts)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_answer(question: str, chunks: list[dict]) -> str:
    """Z generativnim modelom sestavi odgovor na podlagi pridobljenih koščkov."""
    context = _build_context(chunks)
    client = get_client()
    response = client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"KONTEKST (oštevilčeni odlomki):\n{context}\n\n"
                    f"VPRAŠANJE: {question}\n\nODGOVOR:"
                ),
            },
        ],
    )
    return (response.choices[0].message.content or "").strip()
