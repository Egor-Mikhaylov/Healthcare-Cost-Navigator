from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..db import get_session
from ..openai_utils import sql_from_nl

router = APIRouter()


class Question(BaseModel):
    question: str


@router.post("/ask")
async def ask(q: Question, session: AsyncSession = Depends(get_session)):
    sql = sql_from_nl(q.question)
    if not sql:
        raise HTTPException(
            status_code=400,
            detail="I can only help with hospital pricing and quality information.",
        )
    try:
        result = await session.execute(text(sql))
        rows = [dict(row) for row in result.mappings().all()]
        return {"answer": rows}
    except Exception as exc:
        return {"error": str(exc)}
