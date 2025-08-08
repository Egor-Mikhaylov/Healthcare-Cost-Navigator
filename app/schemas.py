from pydantic import BaseModel
from typing import Optional, List


class Rating(BaseModel):
    id: int
    provider_ccn: str
    score: int

    class Config:
        orm_mode = True


class ProviderBase(BaseModel):
    id: int
    name: str
    city: str
    state: str
    zip: str
    drg_code: str
    drg_desc: str
    average_covered_charges: Optional[float] = None
    average_total_payments: Optional[float] = None
    average_medicare_payments: Optional[float] = None
    lat: Optional[float] = None
    lon: Optional[float] = None

    class Config:
        orm_mode = True


class Provider(ProviderBase):
    ratings: List[Rating] = []
