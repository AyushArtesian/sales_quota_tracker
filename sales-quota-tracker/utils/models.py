"""SQLAlchemy ORM models for the quota tracker."""

from sqlalchemy import Column, Float, Integer, String

from .db import Base


class QuotaTarget(Base):
    __tablename__ = "quota_targets"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_name = Column(String(100), nullable=False, index=True)
    members = Column(String(500), nullable=True)
    start_month = Column(String(20), nullable=False, index=True)
    duration_months = Column(Integer, nullable=False, default=1)
    quota = Column(Float, nullable=False, default=0.0)
