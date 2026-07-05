# Zajem, strukturiranje in shranjevanje podatkov o podjetjih z generativno UI

Diplomski prototip aplikacije, ki **avtomatizirano zajame** podatke s spletnih
virov, jih **očisti in razdeli** na smiselne enote, z **generativno umetno
inteligenco strukturira** metapodatke o organizaciji, ter rezultate shrani v
**relacijsko (MySQL)** in **vektorsko (Qdrant)** bazo. Vse je dostopno prek
modernega spletnega vmesnika z **iskanjem po pomenu in po ključnih besedah**.

Celoten sistem je **kontejneriziran** — zažene se z enim ukazom in deluje na
katerikoli napravi z nameščenim Dockerjem.

---

## Arhitektura

```
┌──────────────────────── frontend (React + nginx, vrata 8081) ───────────────────────┐
│  Nadzorna plošča │ Organizacije │ Iskanje (semantično / keyword) │ AI klepet │ Strani │
└───────────────────────────────────────┬──────────────────────────────────────────────┘
                                         │ REST  /api/*
┌──────────────────────────── backend (FastAPI, vrata 8000) ──────────────────────────┐
│  PIPELINE (orkestrator):                                                             │
│   1) ZAJEM (Scrapy) → 2) ČIŠČENJE (BeautifulSoup) → 3) CHUNKING →                    │
│   4) AI EKSTRAKCIJA (OpenAI) → 5) RELACIJSKA BAZA → 6) VEKTORSKA BAZA                │
└───────────────┬──────────────────────────────────────────────┬──────────────────────┘
        ┌────────▼─────────┐                            ┌─────────▼─────────┐
        │  MySQL (8.4)     │                            │  Qdrant (1.12)    │
        │  vrata 3307      │                            │  vrata 6333       │
        │  strukturirano   │                            │  embeddingi       │
        └──────────────────┘                            └───────────────────┘
```

### Moduli (skladno z idejo diplome)

| Modul iz diplome | Kje v kodi |
|---|---|
| Zajem podatkov (web scraping) | `backend/scraper/` (Scrapy, pajek `fei`) |
| Čiščenje in normalizacija | `backend/scraper/scraper/pipelines.py` + `backend/app/pipeline/cleaning.py` |
| Razdelitev na enote (chunking) | `backend/app/pipeline/chunking.py` |
| AI ekstrakcija in strukturiranje | `backend/app/pipeline/extraction.py` (OpenAI) |
| Shranjevanje v relacijsko bazo | `backend/app/models.py` + MySQL |
| Vektorske predstavitve + vektorska baza | `backend/app/pipeline/embedding.py` + `backend/app/vector_store.py` (Qdrant) |
| Pregled, iskanje in prikaz | `frontend/` (React) |
| Povezovanje modulov | `backend/app/pipeline/orchestrator.py` |
| AI klepet (RAG) nad podatki — *bonus* | `backend/app/pipeline/chat.py` + `backend/app/routers/chat.py` |

---

## Predpogoji

- **Docker Desktop** (Windows/Mac) oz. Docker Engine + Docker Compose (Linux).
- **OpenAI API ključ** (za AI strukturiranje in embeddinge).

Nič drugega ni treba nameščati — Python, Node ipd. tečejo znotraj kontejnerjev.

---

## Zagon

```bash
# 1. Pripravi okoljske spremenljivke
cp .env.example .env          # Linux/Mac
# Copy-Item .env.example .env # Windows PowerShell

# 2. V .env vpiši svoj OpenAI ključ
#    OPENAI_API_KEY=sk-...

# 3. Zaženi vse
docker compose up --build
```

Ko se vse zažene, odpri:

| Storitev | Naslov |
|---|---|
| **Spletni vmesnik** | http://localhost:8081 |
| Backend API (Swagger) | http://localhost:8000/docs |
| Qdrant nadzorna plošča | http://localhost:6333/dashboard |
| MySQL | `localhost:3307` (uporabnik `root`, geslo iz `.env`) |

---

## Uporaba

1. V vmesniku odpri **Nadzorna plošča** → klikni **Zaženi zajem**
   (prazno polje = privzeti testni vir **FEI UNM**; lahko vneseš poljuben URL).
2. V realnem času spremljaj dnevnik in korake pipelina.
3. **Organizacije** — strukturirani podatki iz MySQL + iskanje po ključnih besedah.
4. **Iskanje** — preklopi med **semantičnim** (Qdrant, po pomenu) in
   **klasičnim** (MySQL, po ključnih besedah) iskanjem.
5. **AI klepet** — vprašanja v naravnem jeziku nad zajetimi podatki (RAG):
   semantično pridobivanje relevantnih koščkov + generativni odgovor z
   navedbo virov.
6. **Zajete strani** — pregled očiščenega besedila in chunkov.

> Vsak zagon obdela **eno spletno stran/domeno → eno organizacijo + N strani + M chunkov**.
> Za več vrstic v tabeli organizacij poženi pipeline na več različnih spletnih straneh.

---

## Konfiguracija (`.env`)

| Spremenljivka | Privzeto | Opis |
|---|---|---|
| `OPENAI_API_KEY` | — | **obvezno** |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM za strukturiranje |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | model za embeddinge |
| `EMBEDDING_DIM` | `1536` | dimenzija vektorjev (uskladi z embedding modelom) |
| `SCRAPE_MAX_PAGES` | `40` | največ zajetih strani na zagon |
| `SCRAPE_MAX_DEPTH` | `2` | globina sledenja povezavam |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `1200` / `150` | velikost in prekrivanje chunkov |

---

## Pogoste težave

- **Backend se ne zažene takoj** — počaka, da je MySQL pripravljen (healthcheck);
  prvi zagon traja dlje zaradi gradnje slik.
- **AI ekstrakcija / embeddingi ne delujejo** — preveri `OPENAI_API_KEY` v `.env`.
  Pipeline se v tem primeru vseeno izvede (strani in chunki se shranijo), le brez
  strukturiranja in vektorjev.
- **Zajem vrne 0 strani** — ciljna stran morda prepoveduje strganje v `robots.txt`.
  Privzeto ga spoštujemo (`ROBOTSTXT_OBEY = True` v
  `backend/scraper/scraper/settings.py`).
- **Spreminjanje embedding modela** — če zamenjaš na npr. `text-embedding-3-large`,
  nastavi `EMBEDDING_DIM=3072` in pobriši Qdrant volumen
  (`docker compose down -v`).

---

## Struktura projekta

```
.
├── docker-compose.yml        # orkestracija vseh storitev
├── .env.example
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI vstopna točka
│   │   ├── config.py db.py models.py schemas.py vector_store.py openai_client.py
│   │   ├── pipeline/         # cleaning, chunking, extraction, embedding, chat, orchestrator
│   │   └── routers/          # pipeline, organizations, pages, search, chat, meta
│   └── scraper/              # Scrapy projekt (web scraping, pajek "fei")
└── frontend/                 # React + Vite + Tailwind (nginx)
```
