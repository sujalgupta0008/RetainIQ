"""SQLAlchemy models. Every tenant-owned table has tenant_id + index."""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Index, JSON
from datetime import datetime, timezone
from .database import Base


def now():
    # Timezone-aware UTC; stored naive-compatible by SQLAlchemy dialects.
    # (Previously datetime.utcnow(), deprecated in Python 3.12+.)
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    email = Column(String(200), nullable=False)
    pw_hash = Column(String(300), nullable=False)
    salt = Column(String(100), nullable=False)
    role = Column(String(30), default="manager")  # admin|manager|analyst|viewer
    created_at = Column(DateTime, default=now)
    __table_args__ = (Index("ix_users_tenant_email", "tenant_id", "email", unique=True),)

class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    age = Column(Integer, default=35)
    income = Column(Float, default=600000)
    tenure_months = Column(Integer, default=24)
    region = Column(String(60), default="Mumbai")
    segment = Column(String(60), default="Mass")
    created_at = Column(DateTime, default=now)

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False)
    type = Column(String(40), default="savings")
    balance = Column(Float, default=50000)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True, nullable=False)
    category = Column(String(60), default="deposit")

class CustomerProduct(Base):
    __tablename__ = "customer_products"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False)
    amount = Column(Float, nullable=False)
    ts = Column(DateTime, default=now, index=True)
    type = Column(String(30), default="debit")

class Interaction(Base):
    __tablename__ = "interactions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False)
    kind = Column(String(40), default="call", index=True)  # complaint|call|login|visit|fail
    severity = Column(Integer, default=1)
    resolved = Column(Boolean, default=True)
    resolution_days = Column(Float, default=1.0)
    ts = Column(DateTime, default=now, index=True)
    note = Column(Text, default="")

class CustomerFeature(Base):
    __tablename__ = "customer_features"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False, unique=True)
    f = Column(JSON, default=dict)  # 16 features dict
    label = Column(Integer, default=0)  # churned 1/0

class ChurnPrediction(Base):
    __tablename__ = "churn_predictions"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False)
    proba = Column(Float, index=True, nullable=False)
    band = Column(String(20), index=True, default="Low")
    trajectory = Column(JSON, default=dict)  # {d90,d60,d30,today}
    drivers = Column(JSON, default=list)
    explanation = Column(Text, default="")
    created_at = Column(DateTime, default=now, index=True)

class CustomerValue(Base):
    __tablename__ = "customer_values"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False, unique=True)
    clv = Column(Float, default=0)
    annual_contrib = Column(Float, default=0)
    revenue_at_risk = Column(Float, default=0, index=True)

class Recommendation(Base):
    __tablename__ = "retention_recommendations"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False, unique=True)
    action = Column(String(60), nullable=False)
    cost = Column(Float, default=0)
    success = Column(Float, default=0)
    expected_roi = Column(Float, default=0)
    reason = Column(Text, default="")
    priority = Column(String(20), default="Low Priority")
    priority_score = Column(Float, default=0)

class Campaign(Base):
    __tablename__ = "campaigns"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    intervention = Column(String(60), nullable=False)
    audience = Column(JSON, default=dict)  # filters
    offer_cost = Column(Float, default=800)
    expected_success = Column(Float, default=0.25)
    duration_days = Column(Integer, default=30)
    status = Column(String(20), default="draft", index=True)
    created_at = Column(DateTime, default=now)

class CampaignTarget(Base):
    __tablename__ = "campaign_targets"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), index=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), index=True, nullable=False)
    group = Column(String(20), default="treatment")  # treatment|control
    reached = Column(Boolean, default=True)
    retained = Column(Boolean, default=False)

class Experiment(Base):
    __tablename__ = "experiments"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String(150), default="A/B test")
    created_at = Column(DateTime, default=now)

class ExperimentResult(Base):
    __tablename__ = "experiment_results"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id"), nullable=False)
    treat_n = Column(Integer, default=0)
    ctrl_n = Column(Integer, default=0)
    treat_ret = Column(Float, default=0)
    ctrl_ret = Column(Float, default=0)
    lift = Column(Float, default=0)
    revenue = Column(Float, default=0)
    cost = Column(Float, default=0)
    roi = Column(Float, default=0)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer, index=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    action = Column(String(80), nullable=False)
    meta = Column(Text, default="")
    ts = Column(DateTime, default=now, index=True)
