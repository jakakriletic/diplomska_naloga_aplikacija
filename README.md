# Diplomska aplikacija

Enostaven prototip za zajem podatkov s spletnih strani organizacij.

Aplikacija:

- prebere strani z izbrane domene,
- ocisti in razdeli besedilo na manjse dele,
- shrani strani, chunke in organizacije v MySQL,
- po zelji uporabi OpenAI za ekstrakcijo podatkov, embeddinge, semanticno iskanje in AI klepet,
- omogoca pregled podatkov v React vmesniku.

## Kaj rabis

- Docker Desktop ali Docker Engine z Docker Compose
- OpenAI API kljuc, ce zelis uporabljati AI funkcije

Brez OpenAI kljuca se aplikacija se vedno zazene, ampak AI ekstrakcija, embeddingi,
semanticno iskanje in klepet ne bodo delovali.

## Zagon

V korenu projekta naredi `.env`:

```powershell
Copy-Item .env.example .env
```

Na Linuxu ali macOS:

```bash
cp .env.example .env
```

V `.env` nastavi OpenAI kljuc:

```env
OPENAI_API_KEY=sk-...
```

Potem zazeni vse skupaj:

```bash
docker compose up --build
```

Ce hoces zagon v ozadju:

```bash
docker compose up --build -d
```

Odpri:

- aplikacija: http://localhost:8081
- backend docs: http://localhost:8000/docs
- healthcheck: http://localhost:8000/api/health
- Qdrant dashboard: http://localhost:6333/dashboard

## Uporaba

1. Odpri http://localhost:8081.
2. Vnesi URL organizacije ali pusti prazno za testni vir `https://fei.uni-nm.si/`.
3. Po želji nastavi globino zajema (0–5), omejitev strani (1–200) in velikost odseka (300–4000 znakov).
4. Klikni zagon zajema.
5. Po koncu poglej organizacije, zajete strani, iskanje ali AI klepet.

## Ustavitev

```bash
docker compose down
```

Ce zelis pobrisati tudi podatke iz MySQL in Qdranta:

```bash
docker compose down -v
```

## Lokalni razvoj

Najprej zazeni bazi:

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

Frontend pri lokalnem razvoju tece na http://localhost:5173 in posilja API
zahtevke na backend na http://localhost:8000.

## Preverjanje kode

Backend (iz korena projekta):

```powershell
$env:PYTHONPATH="backend"
py -3 -m unittest discover -s backend/tests
```

Frontend:

```bash
cd frontend
npm run lint
npm test
npm run build
```

## Glavne nastavitve

Nastavitve so v `.env`. Najbolj uporabne:

- `OPENAI_API_KEY`: OpenAI API kljuc
- `MYSQL_PORT`: privzeto `3307`
- `BACKEND_PORT`: privzeto `8000`
- `FRONTEND_PORT`: privzeto `8081`
- `BIND_HOST`: privzeto `127.0.0.1`, zato storitve niso izpostavljene lokalnemu omrežju
- `CORS_ORIGINS`: dovoljeni naslovi frontenda, ločeni z vejico
- `SCRAPE_MAX_PAGES`: najvec zajetih strani na en zagon
- `SCRAPE_MAX_DEPTH`: najvecja globina sledenja povezavam

Privzeto globino, omejitev strani in velikost odseka je mogoče pred posameznim
zagonom spremeniti tudi na nadzorni plošči. Vrednosti veljajo samo za novi zagon.

## Struktura

```text
backend/   FastAPI API, pipeline, scraper, MySQL in Qdrant dostop
frontend/  React + Vite vmesnik
docker-compose.yml
.env.example
```
