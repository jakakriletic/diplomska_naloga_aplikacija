"""Izbor in krajšanje spletnih strani za kontekst strukturirane AI-ekstrakcije."""
from __future__ import annotations

EXTRACTION_PAGE_CHARS = 2400

_LEADERSHIP_URL_TERMS = (
    "vodstvo", "uprava", "poslovodstvo", "management", "leadership", "team",
    "organi", "organiziranost",
)
_LEADERSHIP_TEXT_TERMS = (
    "predsednik uprave", "predsednica uprave", "chief executive", " ceo",
    "generalni direktor", "generalna direktorica", "direktor", "direktorica",
    "dekanica", "dekan ",
)
_PROFILE_URL_TERMS = (
    "osebna-izkaznica", "osnovne-informacije", "company-profile", "about-us",
    "o-nas", "o-fakulteti", "o-podjetju", "predstavitev",
)
_CONTACT_URL_TERMS = ("kontakt", "contact", "location", "lokacija", "sedez", "sedež")
_HISTORY_URL_TERMS = ("zgodovina", "history", "ustanovitev", "geschichte")
_ACTIVITY_URL_TERMS = (
    "dejavnost", "services", "storitve", "solutions", "resitve", "rešitve",
    "products", "izdelki", "programi", "study", "studij",
)

# Vrstni red je pomemben: pri krajšanju dolgih strani najprej ohranimo odlomke,
# ki lahko vsebujejo vodilno osebo, nato druge strukturirane kontaktne podatke.
_EXTRACTION_HINTS = (
    "predsednik uprave", "predsednica uprave", "chief executive", "ceo",
    "generalni direktor", "generalna direktorica", "dekanica", "dekan",
    "direktor", "direktorica", "vodstvo", "management", "leadership",
    "kontakt in lokacija", "contact and location", "kontaktni podatki", "contact details",
    "kontakt", "contact",
    "ustanovljen", "ustanovljena", "founded", "established",
    "e-pošta", "e-naslov", "email", "telefon", "phone", "naslov",
    "address", "headquarters", "sedež",
)


def _normalized_url(page: dict) -> str:
    return str(page.get("url", "")).lower().replace("_", "-")


def _contains_url_term(page: dict, terms: tuple[str, ...]) -> bool:
    url = _normalized_url(page)
    return any(term.replace("_", "-") in url for term in terms)


def _contains_text_term(page: dict, terms: tuple[str, ...]) -> bool:
    text = str(page.get("text", "")).lower()
    return any(term in text for term in terms)


def page_excerpt(text: str, limit: int) -> str:
    """Skrajša dolgo stran, vendar ohrani okolico pomembnih metapodatkov."""
    text = text.strip()
    if len(text) <= limit:
        return text
    if limit <= 0:
        return ""

    # Naslov in uvod strani sta skoraj vedno koristna za identiteto organizacije.
    prefix_size = min(600, limit)
    parts = [text[:prefix_size].strip()]
    used_ranges = [(0, prefix_size)]
    remaining = limit - len(parts[0])
    lowered = text.lower()

    for hint in _EXTRACTION_HINTS:
        if remaining <= 5:
            break
        position = lowered.find(hint)
        if position < 0:
            continue

        start = max(0, position - 180)
        end = min(len(text), position + len(hint) + 520)
        if any(start < old_end and end > old_start for old_start, old_end in used_ranges):
            continue

        separator = "\n…\n"
        available = remaining - len(separator)
        if available <= 0:
            break
        part = text[start:end].strip()[:available]
        if not part:
            continue
        parts.append(separator + part)
        used_ranges.append((start, start + len(part)))
        remaining -= len(separator) + len(part)

    # Če na strani ni bilo metapodatkovnih označevalcev, dopolnimo odlomek z
    # začetkom besedila, namesto da bi po nepotrebnem pustili prazen proračun.
    if len(parts) == 1 and remaining > 0:
        parts[0] += text[prefix_size : prefix_size + remaining]

    return "".join(parts)[:limit]


def _category_rank(page: dict, terms: tuple[str, ...]) -> tuple[int, int, int]:
    """Prednost imajo neposredni URL-zadetki, manjša globina in krajše strani."""
    url = _normalized_url(page)
    matching_indexes = [
        index for index, term in enumerate(terms)
        if term.replace("_", "-") in url
    ]
    return (
        min(matching_indexes, default=len(terms)),
        int(page.get("depth", 0)),
        len(str(page.get("text", ""))),
    )


def _ordered_extraction_pages(pages: list[dict]) -> list[dict]:
    """Uravnoteži strani za identiteto, vodstvo, stik, zgodovino in dejavnost."""
    selected: list[dict] = []
    selected_urls: set[str] = set()

    def add_best(candidates: list[dict], terms: tuple[str, ...] = ()) -> None:
        candidates = [p for p in candidates if str(p.get("url", "")) not in selected_urls]
        if not candidates:
            return
        if terms:
            best = min(candidates, key=lambda p: _category_rank(p, terms))
        else:
            best = min(
                candidates,
                key=lambda p: (int(p.get("depth", 0)), len(str(p.get("text", "")))),
            )
        selected.append(best)
        selected_urls.add(str(best.get("url", "")))

    add_best([p for p in pages if int(p.get("depth", 0)) == 0])
    add_best(
        [
            p for p in pages
            if _contains_url_term(p, _LEADERSHIP_URL_TERMS)
            or _contains_text_term(p, _LEADERSHIP_TEXT_TERMS)
        ],
        _LEADERSHIP_URL_TERMS,
    )
    add_best([p for p in pages if _contains_url_term(p, _PROFILE_URL_TERMS)], _PROFILE_URL_TERMS)
    add_best([p for p in pages if _contains_url_term(p, _CONTACT_URL_TERMS)], _CONTACT_URL_TERMS)
    add_best([p for p in pages if _contains_url_term(p, _HISTORY_URL_TERMS)], _HISTORY_URL_TERMS)
    add_best([p for p in pages if _contains_url_term(p, _ACTIVITY_URL_TERMS)], _ACTIVITY_URL_TERMS)

    # Preostanek je rezerva za spletna mesta z neobičajno strukturo URL-jev.
    remaining = [p for p in pages if str(p.get("url", "")) not in selected_urls]
    remaining.sort(key=lambda p: (int(p.get("depth", 0)), -len(str(p.get("text", "")))))
    return selected + remaining


def build_extraction_text(pages: list[dict], max_chars: int) -> str:
    """Sestavi omejen in vsebinsko uravnotežen kontekst za AI-ekstrakcijo."""
    blocks: list[str] = []
    remaining = max_chars
    for page in _ordered_extraction_pages(pages):
        if remaining <= 0:
            break
        separator = "\n\n" if blocks else ""
        header = f"[VIR: {page.get('url', '')}]\n"
        available = remaining - len(separator) - len(header)
        if available <= 0:
            break
        excerpt = page_excerpt(
            str(page.get("text", "")),
            min(EXTRACTION_PAGE_CHARS, available),
        )
        if not excerpt:
            continue
        block = separator + header + excerpt
        blocks.append(block)
        remaining -= len(block)
    return "".join(blocks)
