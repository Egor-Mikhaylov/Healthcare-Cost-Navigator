# Healthcare Cost Navigator

Minimal FastAPI service exposing hospital pricing and quality data.

## Setup
1. Copy `.env.example` to `.env` and fill values.
2. `docker-compose up -d --build`
3. Load seed data:
   ```bash
   # optional: if you want to load a different CMS dump
   export CSV_PATH=data/raw/MUP_INP_RY24_P03_V10_DY22_PrvSvc.csv
   make seed
   ```

If running without Docker, apply database migrations first:

```bash
alembic upgrade head
```

FastAPI runs on [http://localhost:8000](http://localhost:8000).

## Example cURL
```bash
# 1. Providers by DRG code
curl "http://localhost:8000/providers?drg=039"

# 2. Providers near a ZIP within 50 km
curl "http://localhost:8000/providers?zip=36301&radius_km=50"

# 3. Providers by DRG and geography
curl "http://localhost:8000/providers?drg=039&zip=36301&radius_km=50"

# 4. Ask for average covered charges for a DRG
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "What is the average covered charge for DRG 039?"}'

# 5. Ask for highest rated providers
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"question": "Which are the highest rated providers?"}'
```
