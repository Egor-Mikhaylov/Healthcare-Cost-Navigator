"""Load CMS provider CSV into Postgres and seed ratings."""

import asyncio
import csv
import math
import os
import random
from pathlib import Path

import pgeocode

from app.db import AsyncSessionLocal
from app.models import Provider, Rating

CSV_PATH = Path(os.getenv("CSV_PATH", "data/raw/sample_prices_ny.csv"))


def clean_amount(value: str) -> float:
    value = value.replace("$", "").replace(",", "")
    try:
        return float(value)
    except ValueError:
        return 0.0


async def load_csv():
    nomi = pgeocode.Nominatim("us")

    async with AsyncSessionLocal() as session:
        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                zip_code = row["Rndrng_Prvdr_Zip5"]
                loc = nomi.query_postal_code(zip_code)
                lat = None if math.isnan(loc.latitude) else float(loc.latitude)
                lon = None if math.isnan(loc.longitude) else float(loc.longitude)

                avg_cov = clean_amount(
                    row.get("Avg_Submtd_Cvrd_Chrg") or row.get("Avg_Submt_Cvrd_Chrg")
                )
                provider = Provider(
                    provider_ccn=row["Rndrng_Prvdr_CCN"],
                    name=row["Rndrng_Prvdr_Org_Name"],
                    city=row["Rndrng_Prvdr_City"],
                    state=row["Rndrng_Prvdr_State_Abrvtn"],
                    zip=zip_code,
                    drg_code=row["DRG_Cd"],
                    drg_desc=row["DRG_Desc"],
                    average_covered_charges=avg_cov,
                    average_total_payments=clean_amount(row["Avg_Tot_Pymt_Amt"]),
                    average_medicare_payments=clean_amount(row["Avg_Mdcr_Pymt_Amt"]),
                    lat=lat,
                    lon=lon,
                )
                session.add(provider)
                rating = Rating(
                    provider_ccn=provider.provider_ccn, score=random.randint(1, 10)
                )
                session.add(rating)
        await session.commit()


def main():
    asyncio.run(load_csv())


if __name__ == "__main__":
    main()
