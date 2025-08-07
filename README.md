# Healthcare Cost Navigator

Minimal FastAPI service that lets patients

* look up hospital **prices & quality** (`GET /providers`)
* ask **natural‑language** questions (`POST /ask`)

Built with Python 3.11, FastAPI, async SQLAlchemy 2, PostgreSQL 15, and an optional OpenAI integration.

---

## Quick‑start (🐳 Docker)

```bash
# 1 – copy env template and add your OpenAI key if you have one
cp .env.example .env

# 2 – build + start db + api
docker compose up -d --build

# 3 – create tables & seed sample data
docker compose exec web alembic upgrade head
docker compose exec web python etl.py      # CSV_LIMIT defaults to 40 000
```

API lives at **[http://localhost:8000](http://localhost:8000)**  • Docs at **/docs**

---

## Local dev (no Docker)

```bash
pip install -r requirements.txt
export DB_URL=postgresql+asyncpg://postgres:postgres@localhost/postgres
alembic upgrade head            # create tables
python etl.py                   # seed 100 k rows (set CSV_LIMIT=0 for full load)
uvicorn app.main:app --reload
```

---

## Environment vars

| Var              | Default                                                   | Purpose                                       |
| ---------------- | --------------------------------------------------------- | --------------------------------------------- |
| `DB_URL`         | `postgresql+asyncpg://postgres:postgres@db:5432/postgres` | async URL for the app                         |
| `ALEMBIC_DB_URL` | *none*                                                    | sync URL override for Alembic (rarely needed) |
| `OPENAI_API_KEY` | *empty*                                                   | enables NL→SQL via OpenAI when present        |
| `CSV_PATH`       | `data/raw/sample_prices_ny.csv`                           | alternate CMS dump                            |
| `CSV_LIMIT`      | `100000`                                                  | rows of CSV to process (0 = all)              |

---

## Sample cURL – **all endpoints**

```bash
# ─────  GET /providers  ───────────────────────────────────────────────
# 1. By DRG code only
curl "http://localhost:8000/providers?drg=039"

# 2. Providers near a ZIP within 50 km
curl "http://localhost:8000/providers?zip=36301&radius_km=50"

# 3. Combined DRG + geography search
curl "http://localhost:8000/providers?drg=470&zip=10001&radius_km=40"

# ─────  POST /ask  ───────────────────────────────────────────────────
# 4. Average covered charge for a DRG (NL → SQL)
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question":"What is the average covered charge for DRG 039?"}'

# 5. Cheapest hospital for a DRG within 25 mi of a ZIP
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question":"Who is cheapest for DRG 470 within 25 miles of 10001?"}'

# 6. Highest‑rated providers overall
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
     -d '{"question":"Which are the highest rated providers?"}'
```

---

## Extra NL prompts you can try

| Prompt                                                                | What it should do                      |
| --------------------------------------------------------------------- | -------------------------------------- |
| “Which hospitals have the best ratings for heart surgery near 10032?” | quality query with location filter     |
| “Show the average Medicare payment for DRG 039.”                      | aggregates `average_medicare_payments` |
| “Hospitals within 30 km of 60606 for knee replacement”                | DRG 470 + radius                       |
| “What’s the weather today?”                                           | out‑of‑scope fallback message          |

---

## Dev notes & trade‑offs

* Loader keeps only **unique `provider_ccn`** rows; duplicate DRG records are collapsed.
* Alembic uses a **sync** Postgres driver while the runtime uses `asyncpg`.
* Without an OpenAI key, `/ask` falls back to deterministic regex→SQL rules.
* For production you’d index lat/lon with PostGIS and use pg\_trgm for fuzzy DRG text.

---

### Makefile helpers

```make
seed:          # re‑creates tables + loads CSV_LIMIT rows
	docker compose exec web alembic upgrade head
	docker compose exec web python etl.py

reset:         # drop, recreate, reseed
	docker compose exec db psql -U postgres -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	make seed
```

---

