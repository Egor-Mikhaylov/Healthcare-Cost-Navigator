from typing import List, Optional

from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Provider


async def fetch_providers(
    session: AsyncSession, drg: Optional[str] = None
) -> List[Provider]:
    stmt = select(Provider)
    if drg:
        stmt = stmt.where(
            or_(
                Provider.drg_code == drg,
                Provider.drg_desc.ilike(f"%{drg}%"),
            )
        )
    result = await session.execute(stmt)
    return result.scalars().all()
