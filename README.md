# Zajem in strukturiranje podatkov o organizacijah z generativno umetno inteligenco

Diplomski prototip aplikacije za avtomatiziran zajem podatkov s spletnih strani
organizacij ali podjetij. Sistem strani zajame s Scrapyjem, HTML očisti,
besedilo razdeli na chunke, z OpenAI modelom poskusi izluščiti strukturirane
metapodatke o organizaciji ter podatke shrani v MySQL in Qdrant.

Frontend omogoča zagon obdelave, pregled zajetih strani in organizacij,
iskanje po ključnih besedah, semantično iskanje po vektorjih ter AI klepet nad
zajetimi podatki.

## Arhitektura

Projekt je primarno pripravljen za zagon z Docker Compose:

| Storitev | Tehnologija | Namen | Privzeta vrata na gostitelju |
|---|---|---|---|
| `frontend` | React + Vite, v produkciji nginx | spletni vmesnik in proxy za `/api/*` | `8081` |
| `backend` | FastAPI | REST API in orkestracija pipelina | `8000` |
| `mysql` | MySQL 8.4 | relacijski podatki: zagoni, organizacije, strani, chunki | `3307` |
| `qdrant` | Qdrant 1.12 | vektorji chunkov za semantično iskanje | `6333` |

Pretok podatkov:

```text
Frontend (/api/*)
    -> FastAPI backend
        -> Scrapy zajem spletnih strani
        -> čiščenje in normalizacija besedila
        -> shranjevanje strani v MySQL
        -> AI ekstrakcija metapodatkov organizacije v MySQL
        -> chunking besedila in shranjevanje chunkov v MySQL
        -> OpenAI embeddingi in shranjevanje v Qdrant
```

## Moduli v kodi

| Del sistema | Kje je implementiran |
|---|---|
| Web scraping | `backend/scraper/`, pajek `fei` |
| Čiščenje HTML-a | `backend/scraper/scraper/pipelines.py` |
| Normalizacija besedila | `backend/app/pipeline/cleaning.py` |
| Chunking | `backend/app/pipeline/chunking.py` |
| AI ekstrakcija metapodatkov | `backend/app/pipeline/extraction.py` |
| Embeddingi | `backend/app/pipeline/embedding.py` |
| Qdrant dostop | `backend/app/vector_store.py` |
| Orkestracija pipelina | `backend/app/pipeline/orchestrator.py` |
| AI klepet (RAG) | `backend/app/pipeline/chat.py`, `backend/app/routers/chat.py` |
| Spletni vmesnik | `frontend/` |

## Predpogoji

- Docker Desktop oziroma Docker Engine z Docker Compose.
- OpenAI API ključ za AI ekstrakcijo, embeddinge, semantično iskanje in AI klepet.

OpenAI ključ ni potreben za sam zagon kontejnerjev. Brez njega lahko pipeline še
vedno zajame strani in ustvari chunke, vendar ne bo ustvaril strukturirane
organizacije, vektorjev, semantičnega iskanja ali RAG odgovorov.

## Zagon z Docker Compose

V korenu projekta:

```bash
cp .env.example .env
```

V Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

V datoteki `.env` zamenjaj placeholder:

```env
OPENAI_API_KEY=sk-...
```

Nato zaženi vse storitve:

```bash
docker compose up --build
```

Za zagon v ozadju lahko uporabiš:

```bash
docker compose up --build -d
```

Uporabni naslovi po zagonu:

| Storitev | Naslov |
|---|---|
| Spletni vmesnik | http://localhost:8081 |
| Backend Swagger dokumentacija | http://localhost:8000/docs |
| Backend healthcheck | http://localhost:8000/api/health |
| Qdrant dashboard | http://localhost:6333/dashboard |
| MySQL | `localhost:3307`, uporabnik `root`, geslo iz `.env` |

Ustavitev storitev:

```bash
docker compose down
```

Če želiš pobrisati tudi podatkovna volumna MySQL in Qdrant:

```bash
docker compose down -v
```

## Uporaba aplikacije

1. Odpri http://localhost:8081.
2. Na zavihku **Nadzorna plošča** vnesi URL in klikni **Zaženi zajem**.
3. Če URL pustiš prazen, se uporabi privzeti testni vir `https://fei.uni-nm.si/`.
4. Zajem ostane znotraj iste domene, spoštuje `robots.txt`, preskoči statične datoteke in uporablja omejitve iz `.env`.
5. Po končanem zagonu preglej:
   - **Organizacije**: strukturirani metapodatki iz MySQL,
   - **Iskanje**: semantično iskanje prek Qdranta ali klasično iskanje po chunkih v MySQL,
   - **AI klepet**: RAG odgovor na podlagi vektorsko najdenih chunkov,
   - **Zajete strani**: očiščeno besedilo in ustvarjeni chunki.

Vsak uspešen zagon poskusi ustvariti en zapis organizacije ter poljubno število
zajetih strani in chunkov. Če AI ekstrakcija ne uspe, se strani in chunki vseeno
shranijo.

## Konfiguracija

Spremenljivke so definirane v `.env.example` in jih Docker Compose posreduje
kontejnerjem.

| Spremenljivka | Privzeto | Opis |
|---|---|---|
| `OPENAI_API_KEY` | `sk-...` | OpenAI API ključ. Placeholder zamenjaj z dejansko vrednostjo ali pusti prazno, če AI funkcij ne uporabljaš. |
| `OPENAI_MODEL` | `gpt-4o-mini` | model za ekstrakcijo metapodatkov in AI klepet |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | model za embeddinge |
| `EMBEDDING_DIM` | `1536` | dimenzija vektorjev v Qdrantu; mora ustrezati embedding modelu |
| `MYSQL_ROOT_PASSWORD` | `rootpass` | geslo uporabnika `root` v MySQL |
| `MYSQL_DATABASE` | `companiesdb` | ime MySQL baze |
| `MYSQL_PORT` | `3307` | vrata MySQL na gostitelju |
| `QDRANT_HTTP_PORT` | `6333` | vrata Qdrant HTTP API in dashboarda na gostitelju |
| `QDRANT_COLLECTION` | `company_chunks` | ime Qdrant kolekcije |
| `BACKEND_PORT` | `8000` | vrata FastAPI backenda na gostitelju |
| `FRONTEND_PORT` | `8081` | vrata spletnega vmesnika na gostitelju |
| `SCRAPE_MAX_PAGES` | `40` | največ zajetih strani na en zagon |
| `SCRAPE_MAX_DEPTH` | `2` | največja globina sledenja povezavam |
| `CHUNK_SIZE` | `1200` | ciljna velikost chunka v znakih |
| `CHUNK_OVERLAP` | `150` | prekrivanje med sosednjimi chunki v znakih |

Backend znotraj Docker omrežja uporablja `MYSQL_HOST=mysql`, `MYSQL_PORT=3306`
in `QDRANT_URL=http://qdrant:6333`; teh vrednosti pri običajnem Compose zagonu
ni treba nastavljati v `.env`.

## API poti

Najbolj uporabne poti:

| Metoda | Pot | Namen |
|---|---|---|
| `GET` | `/api/health` | preverjanje delovanja backenda |
| `GET` | `/api/stats` | agregirana statistika za nadzorno ploščo |
| `POST` | `/api/pipeline/run` | zagon pipelina, telo: `{ "url": "https://..." }` ali `{ "url": null }` |
| `GET` | `/api/pipeline/latest` | zadnji zagon |
| `GET` | `/api/pipeline/runs/{run_id}` | podrobnosti zagona z dnevnikom |
| `GET` | `/api/organizations` | seznam organizacij, opcijsko `?q=...` |
| `GET` | `/api/pages` | seznam zajetih strani |
| `GET` | `/api/pages/{page_id}` | očiščeno besedilo strani |
| `GET` | `/api/pages/{page_id}/chunks` | chunki strani |
| `GET` | `/api/search/keyword?q=...` | iskanje po ključnih besedah v MySQL |
| `GET` | `/api/search/semantic?q=...` | semantično iskanje v Qdrantu |
| `POST` | `/api/chat` | AI klepet nad zajetimi podatki |

## Lokalni razvoj

Docker Compose je priporočena pot. Če želiš poganjati frontend in backend
lokalno, najprej zaženi samo bazi:

```bash
docker compose up -d mysql qdrant
```

Backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:MYSQL_HOST="localhost"
$env:MYSQL_PORT="3307"
$env:QDRANT_URL="http://localhost:6333"
$env:OPENAI_API_KEY="sk-..."
uvicorn app.main:app --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Vite teče na http://localhost:5173 in ima proxy za `/api` na
http://localhost:8000.

## Pogoste težave

- **Backend se ne odpre takoj**: prvi zagon traja dlje zaradi gradnje slik in
  čakanja na MySQL healthcheck.
- **AI ekstrakcija, semantično iskanje ali klepet ne delujejo**: preveri, ali je
  `OPENAI_API_KEY` nastavljen na dejanski ključ in ne na `sk-...`.
- **Zajem vrne 0 uporabnih strani**: ciljna stran lahko blokira crawler,
  prepoveduje zajem z `robots.txt`, vrača premalo besedila ali potrebuje
  JavaScript renderiranje, ki ga ta Scrapy crawler ne izvaja.
- **Po menjavi embedding modela dobivaš napake v Qdrantu**: uskladi
  `EMBEDDING_DIM` z novim modelom in ponovno ustvari Qdrant volumen z
  `docker compose down -v`.

## Struktura projekta

```text
.
├── .env.example
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── vector_store.py
│   │   ├── pipeline/
│   │   └── routers/
│   └── scraper/
│       ├── scrapy.cfg
│       └── scraper/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    └── src/
```
