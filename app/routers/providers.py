from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import math
import pgeocode

from ..db import get_session
from .. import schemas, crud

router = APIRouter()


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points in kilometers."""
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


@router.get("/providers", response_model=List[schemas.ProviderBase])
async def list_providers(
    drg: Optional[str] = None,
    zip: Optional[str] = None,
    radius_km: Optional[float] = Query(default=None, gt=0),
    session: AsyncSession = Depends(get_session),
):
    providers = await crud.fetch_providers(session, drg)

    if zip and radius_km is not None:
        nomi = pgeocode.Nominatim("us")
        origin = nomi.query_postal_code(zip)
        if not math.isnan(origin.latitude) and not math.isnan(origin.longitude):
            lat1, lon1 = origin.latitude, origin.longitude
            providers = [
                p
                for p in providers
                if p.lat is not None
                and p.lon is not None
                and haversine(lat1, lon1, p.lat, p.lon) <= radius_km
            ]

    providers.sort(key=lambda p: p.average_covered_charges or 0)
    return providers
