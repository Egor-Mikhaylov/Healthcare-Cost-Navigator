import os
import re
from typing import Optional

try:
    import openai
except ImportError:  # optional dependency
    openai = None

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if openai and OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY


def sql_from_nl(question: str) -> Optional[str]:
    """Very small helper translating natural language to SQL.
    Falls back to a deterministic mapping when OpenAI is not available."""
    q = question.lower()
    # simple guardrails
    keywords = [
        "hospital",
        "pricing",
        "price",
        "cost",
        "charge",
        "payment",
        "rating",
        "quality",
    ]
    if not any(k in q for k in keywords):
        return None

    # basic patterns
    m = re.search(r"drg\s*(\d+)", q)
    if m and "average" in q and "charge" in q:
        drg = m.group(1)
        return f"SELECT AVG(average_covered_charges) AS avg_charge FROM providers WHERE drg_code = '{drg}'"

    if "highest rated" in q:
        return (
            "SELECT p.name, r.score FROM providers p JOIN ratings r ON p.provider_ccn = r.provider_ccn "
            "ORDER BY r.score DESC LIMIT 5"
        )

    if openai and OPENAI_API_KEY:
        prompt = (
            "Translate the user question into a SQL query for a PostgreSQL database. "
            "The database has tables 'providers' and 'ratings'.\n"
            "Schema: providers(id, name, city, state, zip, drg_code, drg_desc, "
            "average_covered_charges, average_total_payments, average_medicare_payments, lat, lon, provider_ccn); "
            "ratings(id, provider_ccn, score). Return ONLY the SQL."
        )
        resp = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            temperature=0,
        )
        sql = resp.choices[0].message["content"].strip()
        return sql

    return None
