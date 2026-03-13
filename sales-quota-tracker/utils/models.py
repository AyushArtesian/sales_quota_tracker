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


class ClientMaster(Base):
    __tablename__ = "client_master"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(100), nullable=False, unique=True, index=True)
    client_name = Column(String(200), nullable=False, index=True)
    acquisition_date = Column(String(20), nullable=True)
    consideration_expiration_month = Column(String(20), nullable=True)


class BillingData(Base):
    __tablename__ = "billing_data"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(20), nullable=False)
    type = Column(String(100), nullable=True)
    description = Column(String(500), nullable=True)
    sales_person = Column(String(100), nullable=False, index=True)
    sales_team = Column(String(100), nullable=True, index=True)
    billing_amount = Column(Float, nullable=False)
    month = Column(String(20), nullable=False, index=True)
    client_name = Column(String(200), nullable=False, index=True)
    client_onboarding_date = Column(String(20), nullable=True)
    consideration_expiration_month = Column(String(20), nullable=True)
