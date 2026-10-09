from pydantic import BaseModel, Field, field_validator
from typing import Optional

ALLOWED_ROLES = ("manager", "analyst", "viewer")  # NOTE: 'admin' intentionally excluded —
# self-registration as admin is a privilege-escalation vector (see routes/auth.py).


class RegisterIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=8, max_length=128)
    tenant: Optional[str] = Field(default=None, max_length=100)
    role: str = Field(default="manager", max_length=30)

    @field_validator("email")
    @classmethod
    def _email_valid(cls, v: str) -> str:
        v = v.strip().lower()
        # Minimal RFC-lite check without extra deps (no email-validator required).
        if "@" not in v or "." not in v.split("@")[-1] or " " in v:
            raise ValueError("Invalid email address")
        return v

    @field_validator("role")
    @classmethod
    def _role_allowed(cls, v: str) -> str:
        v = (v or "manager").strip().lower()
        if v not in ALLOWED_ROLES:
            # Unknown/admin roles fall back to least-privilege default instead of failing
            # open-registration flows. Admins are created out-of-band / via seed.
            return "manager"
        return v

    @field_validator("password")
    @classmethod
    def _pw_not_trivial(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Password must not be blank")
        return v


class LoginIn(BaseModel):
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=1, max_length=128)


class GoogleIn(BaseModel):
    credential: str = Field(min_length=10, max_length=8000)


class RoiIn(BaseModel):
    min_proba: float = Field(default=0.4, ge=0.0, le=1.0)
    min_clv: float = Field(default=0, ge=0, le=1e12)
    segment: Optional[str] = Field(default=None, max_length=60)
    intervention_cost: float = Field(default=800, ge=0, le=1e8)
    success_rate: float = Field(default=0.25, ge=0.0, le=1.0)
    reach: float = Field(default=1.0, ge=0.01, le=1.0)


class CampaignIn(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    intervention: str = Field(default="cashback", max_length=60)
    min_proba: float = Field(default=0.4, ge=0.0, le=1.0)
    min_clv: float = Field(default=0, ge=0, le=1e12)
    segment: Optional[str] = Field(default=None, max_length=60)
    product: Optional[str] = Field(default=None, max_length=80)
    offer_cost: float = Field(default=800, ge=0, le=1e8)
    expected_success: float = Field(default=0.25, ge=0.0, le=1.0)
    duration_days: int = Field(default=30, ge=1, le=365)


class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)


class UploadRow(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    age: int = Field(default=35, ge=0, le=120)
    income: float = Field(default=600000, ge=0, le=1e12)
    tenure_months: int = Field(default=24, ge=0, le=600)
    region: str = Field(default="Mumbai", max_length=60)
    avg_balance: float = Field(default=50000, ge=0, le=1e12)
    txn_freq: float = Field(default=8, ge=0, le=10000)
    avg_txn: float = Field(default=4000, ge=0, le=1e12)

