import os, re
from typing import Optional

# ------------------------------------------------------------------#
# OpenAI ≥ 1.0 client                                               #
# ------------------------------------------------------------------#
try:
    from openai import OpenAI                     # pip install openai>=1.0
    _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    _client = None                                # lib not installed or no key


# ------------------------------------------------------------------#
# NL → SQL helper                                                   #
# ------------------------------------------------------------------#
def sql_from_nl(question: str) -> Optional[str]:
    """
    Translate a natural-language question into a SQL string.

    • Uses ChatGPT when an API key is configured.
    • Falls back to a handful of deterministic shortcuts otherwise.
    • Returns None for out-of-scope questions (the /ask router then
      sends its “I can only help …” message).
    """
    q = question.lower().strip()

    # ----- guard-rail: quickly drop non-healthcare queries ----------
    if not any(k in q for k in (
        "hospital", "pricing", "price", "cost", "charge", "payment",
        "rating", "rated", "quality", "cheapest", "lowest", "provider"
    )):
        return None

    # ---------- regex shortcuts (no OpenAI needed) ------------------
    m_drg = re.search(r"drg\s*(\d+)", q)

    # Average covered charge for a DRG
    if m_drg and "average" in q and "charge" in q:
        drg = m_drg.group(1)
        return (
            "SELECT AVG(average_covered_charges) AS avg_charge "
            "FROM providers WHERE drg_code = '{drg}'"
        ).format(drg=drg)

    # Highest-rated providers
    if any(p in q for p in ("highest rated", "best ratings", "best rating")):
        return (
            "SELECT p.name, r.score "
            "FROM providers p "
            "JOIN ratings r ON p.provider_ccn = r.provider_ccn "
            "ORDER BY r.score DESC LIMIT 5"
        )

    # Cheapest / lowest-cost providers for a DRG
    if m_drg and any(p in q for p in ("cheapest", "lowest", "lowest cost")):
        drg = m_drg.group(1)
        return (
            "SELECT p.name, p.average_covered_charges AS cost "
            "FROM providers p "
            "WHERE p.drg_code = '{drg}' "
            "ORDER BY cost ASC LIMIT 5"
        ).format(drg=drg)

    # ---------- OpenAI path (flexible NL) ---------------------------
    if _client:
        prompt = (
            "Translate the user's question into a SQL query for PostgreSQL. "
            "Use ONLY the columns and tables provided and return ONLY SQL.\n\n"
            "Table providers(id, name, city, state, zip, drg_code, drg_desc, "
            "average_covered_charges, average_total_payments, "
            "average_medicare_payments, lat, lon, provider_ccn)\n"
            "Table ratings(id, provider_ccn, score)\n"
        )
        try:
            resp = _client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user",   "content": question},
                ],
                temperature=0,
            )
            sql = resp.choices[0].message.content.strip()

            # Remove ```sql … ``` fences if the model added them
            if sql.startswith("```"):
                sql = (
                    sql.lstrip("`")     # leading back-ticks
                       .lstrip("sql")   # optional “sql” tag
                       .strip("`")      # trailing back-ticks
                       .strip()
                )
            return sql
        except Exception as exc:
            # Log and let the router show the fallback message
            print("OpenAI error:", exc)

    return None
