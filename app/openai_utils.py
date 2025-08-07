import os
import re
from typing import Optional

# ------------------------------------------------------------------
# OpenAI ≥ 1.0 client ----------------------------------------------
# ------------------------------------------------------------------
try:
    from openai import OpenAI            # pip install openai>=1.0
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:                        # no package or no key
    _client = None

# ------------------------------------------------------------------
# NL → SQL helper ---------------------------------------------------
# ------------------------------------------------------------------
def sql_from_nl(question: str) -> Optional[str]:
    """
    Translate a natural-language question into a SQL string.
    • Uses OpenAI if a key/client is available.
    • Otherwise falls back to a few deterministic regex shortcuts.
    """
    q = question.lower()

    # Guardrail: ignore obvious out-of-scope queries
    if not any(k in q for k in (
        "hospital", "pricing", "price", "cost",
        "charge",  "payment", "rating", "rated",
        "provider", "providers", "quality",
    )):
        return None

    # ---------- Hard-coded shortcuts (no API key needed) ----------
    m = re.search(r"drg\s*(\d+)", q)
    if m and "average" in q and "charge" in q:
        drg = m.group(1)
        return (
            "SELECT AVG(average_covered_charges) AS avg_charge "
            "FROM providers WHERE drg_code = '{drg}'"
        ).format(drg=drg)

    if any(phrase in q for phrase in ("highest rated", "best ratings", "best rating")):
        return (
            "SELECT p.name, r.score "
            "FROM providers p "
            "JOIN ratings r ON p.provider_ccn = r.provider_ccn "
            "ORDER BY r.score DESC LIMIT 5"
        )

    # ---------- OpenAI path ---------------------------------------
    if _client:
        prompt = (
            "Translate the user question into a SQL query for a PostgreSQL database. "
            "The database has tables 'providers' and 'ratings'.\n"
            "Schema: providers(id, name, city, state, zip, drg_code, drg_desc, "
            "average_covered_charges, average_total_payments, average_medicare_payments, "
            "lat, lon, provider_ccn); ratings(id, provider_ccn, score).\n"
            "Return ONLY the SQL."
        )
        try:
            resp = _client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            # Log & fall back to “I can’t help” pathway
            print("OpenAI error:", exc)

    return None
