# Prime-Transaction: Finnhub API data fetcher

Mini-aplicatie full-stack care ia date din **Finnhub API**, cu ajutorul unor endpoint-uri non-premium (`company_profile2`, `quote`, `symbol_lookup`), le stocheaza intr-o baza de date de tip **SQLite**, expune datele prin intermediul **FastAPI** si le trimite in frontend (**Next.js**). Datele contin informatii despre preturile actiunilor si modificarile acestora in timp real, ajutand utilizatorul cu privire la o eventuala cumparare. Totul este rulat containerizat (backend + ingest script + frontend + seed optional care stocheaza static 50 de company profiles pentru a evita API timeout sau stocarea a prea multe date).

## Arhitectură (pe scurt)

- **FastAPI (backend)**: citește din SQLite și expune endpoint‑uri pentru stocks/quotes/watchlist/search.
- **Ingest (worker)**: rulează periodic, citește simbolurile din tabela `watchlist` și face refresh în DB din Finnhub.
- **Seed_watchlist_top**: stocheaza la inceput static 50 de valori in DB, pentru a evita supraincarcarea de date si un eventual API timeout.
- **SQLite**: persistată într-un Docker volume (`db_data`), deci datele rămân între restarturi.
- **Next.js (frontend)**: UI care consumă endpoint‑urile backend‑ului.

---

## Cerințe
- Docker + Docker Compose (plugin `docker compose`)
- Cheie Finnhub: `FINNHUB_API_KEY`
---

## Rulare cu Docker

# 1) Creezi un fisier `.env` local in care adaugi API key-ul Finnhub
FINNHUB_API_KEY="API KEY"

# 2) Rulare cu seed (creează DB + populează watchlist cu ~50 simboluri + initiaza aplicatia - Frontend+Backend)
docker compose --profile seed up --build

# 2.1) Rulare fara seed (DB va fi initial gol, utilizatorul poate adauga din search companiile care prezinta interes)
docker compose up --build

# 3) Pornesti aplicatia (port 3000)
- UI: http://localhost:3000
- Backend health: http://localhost:8000/health
