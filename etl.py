"""Load ≤N rows of the CMS CSV into Postgres and seed ratings."""

import asyncio, csv, math, os, random
from pathlib import Path
from time import perf_counter

import pgeocode
from sqlalchemy import text

from app.db import AsyncSessionLocal
from app.models import Provider, Rating

CSV_PATH  = Path(os.getenv("CSV_PATH", "data/raw/sample_prices_ny.csv"))
ROW_LIMIT = int(os.getenv("CSV_LIMIT", "100000"))  # 0 = no limit ⇒ load all rows


def clean_amount(val: str) -> float:
    val = val.replace("$", "").replace(",", "")
    try:
        return float(val)
    except ValueError:
        return 0.0


async def load_csv() -> None:
    nomi   = pgeocode.Nominatim("us")
    start  = perf_counter()
    seen   = set()
    rows   = 0

    # ---- open CSV (sync) ------------------------------------------
    with open(CSV_PATH, newline="", encoding="latin-1") as f:
        reader = csv.DictReader(f)

        # ---- open DB session (async) ------------------------------
        async with AsyncSessionLocal() as sess:

            # ❶  make seeding idempotent: clear existing data
            await sess.execute(text("TRUNCATE ratings, providers CASCADE"))
            await sess.commit()

            # ❷  load up to ROW_LIMIT unique providers
            for rows, row in enumerate(reader, start=1):
                if ROW_LIMIT and rows > ROW_LIMIT:
                    break

                ccn = row["Rndrng_Prvdr_CCN"]
                if ccn in seen:
                    continue
                seen.add(ccn)

                zip_code = row["Rndrng_Prvdr_Zip5"]
                loc      = nomi.query_postal_code(zip_code)
                lat      = None if math.isnan(loc.latitude)  else float(loc.latitude)
                lon      = None if math.isnan(loc.longitude) else float(loc.longitude)

                sess.add(
                    Provider(
                        provider_ccn=ccn,
                        name=row["Rndrng_Prvdr_Org_Name"],
                        city=row["Rndrng_Prvdr_City"],
                        state=row["Rndrng_Prvdr_State_Abrvtn"],
                        zip=zip_code,
                        drg_code=row["DRG_Cd"],
                        drg_desc=row["DRG_Desc"],
                        average_covered_charges=clean_amount(
                            row.get("Avg_Submtd_Cvrd_Chrg") or row.get("Avg_Submt_Cvrd_Chrg")
                        ),
                        average_total_payments=clean_amount(row["Avg_Tot_Pymt_Amt"]),
                        average_medicare_payments=clean_amount(row["Avg_Mdcr_Pymt_Amt"]),
                        lat=lat,
                        lon=lon,
                    )
                )
                sess.add(Rating(provider_ccn=ccn, score=random.randint(1, 10)))

                if rows % 1_000 == 0:
                    print(f"Processed {rows:,} CSV lines…", flush=True)

            await sess.commit()

    elapsed = perf_counter() - start
    print(
        f"Finished: {len(seen):,} unique providers inserted "
        f"from {rows:,} CSV rows in {elapsed:.1f}s (limit={ROW_LIMIT})"
    )


def main() -> None:
    asyncio.run(load_csv())


if __name__ == "__main__":
    main()
