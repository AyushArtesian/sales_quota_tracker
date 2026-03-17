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


class QuotaAchievement(Base):
    __tablename__ = "quota_achievement"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_name = Column(String(100), nullable=False, index=True)
    members = Column(String(500), nullable=True)
    start_month = Column(String(20), nullable=False, index=True)
    duration_months = Column(Integer, nullable=False, default=1)
    quota = Column(Float, nullable=False, default=0.0)
    total_billing = Column(Float, nullable=False, default=0.0)
    new_client_billing = Column(Float, nullable=False, default=0.0)
    existing_client_billing = Column(Float, nullable=False, default=0.0)
    achievement_pct = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="")
    clients_count = Column(Integer, nullable=False, default=0)
    new_client_count = Column(Integer, nullable=False, default=0)


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    rank = Column(Integer, nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_name = Column(String(100), nullable=False)
    achievement_pct = Column(Float, nullable=False)
    total_billing = Column(Float, nullable=False)
    quota = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)


class SalespersonBilling(Base):
    __tablename__ = "salesperson_billing"

    id = Column(Integer, primary_key=True, index=True)
    sales_person = Column(String(100), nullable=False, index=True)
    total_billing = Column(Float, nullable=False)
    billing_count = Column(Integer, nullable=False)
