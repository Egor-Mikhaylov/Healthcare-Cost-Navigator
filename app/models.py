from sqlalchemy import Column, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .db import Base


class Provider(Base):
    __tablename__ = "providers"

    id = Column(Integer, primary_key=True, index=True)
    provider_ccn = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    zip = Column(String, nullable=False)
    drg_code = Column(String, nullable=False)
    drg_desc = Column(String, nullable=False)
    average_covered_charges = Column(Float)
    average_total_payments = Column(Float)
    average_medicare_payments = Column(Float)
    lat = Column(Float)
    lon = Column(Float)

    ratings = relationship(
        "Rating",
        back_populates="provider",
        cascade="all, delete-orphan",
        primaryjoin="Provider.provider_ccn==Rating.provider_ccn",
    )


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    provider_ccn = Column(
        String, ForeignKey("providers.provider_ccn", ondelete="CASCADE"), nullable=False
    )
    score = Column(Integer, nullable=False)

    provider = relationship(
        "Provider",
        back_populates="ratings",
        primaryjoin="Rating.provider_ccn==Provider.provider_ccn",
    )
