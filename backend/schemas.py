from pydantic import BaseModel, Field
from typing import Optional

class RegisterIn(BaseModel):
    email: str; password: str; tenant: Optional[str] = None; role: str = "manager"
class LoginIn(BaseModel):
    email: str; password: str
class RoiIn(BaseModel):
    min_proba: float = 0.4
    min_clv: float = 0
    segment: Optional[str] = None
    intervention_cost: float = 800
    success_rate: float = 0.25
    reach: float = 1.0
class CampaignIn(BaseModel):
    name: str
    intervention: str = "cashback"
    min_proba: float = 0.4
    min_clv: float = 0
    segment: Optional[str] = None
    product: Optional[str] = None
    offer_cost: float = 800
    expected_success: float = 0.25
    duration_days: int = 30
class AskIn(BaseModel):
    question: str = Field(min_length=2, max_length=500)
class UploadRow(BaseModel):
    name: str; age: int = 35; income: float = 600000
    tenure_months: int = 24; region: str = "Mumbai"; avg_balance: float = 50000
    txn_freq: float = 8; avg_txn: float = 4000
