from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from app.models.models import TransactionType, TransactionCategory


# ── Auth ──────────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    monthly_income: float = Field(ge=0)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    monthly_income: float
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# ── Transactions ──────────────────────────────────────────────────────────────


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    type: TransactionType
    category: Optional[TransactionCategory] = TransactionCategory.other  # optional
    description: str  # required now
    date: Optional[datetime] = None

class TransactionOut(TransactionCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Loans ─────────────────────────────────────────────────────────────────────

class LoanCreate(BaseModel):
    name: str
    principal: float = Field(gt=0)
    outstanding: float = Field(gt=0)
    interest_rate: float = Field(gt=0, le=100)
    monthly_emi: float = Field(gt=0)
    tenure_months_remaining: int = Field(gt=0)


class LoanOut(LoanCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    name: str
    target_amount: float = Field(gt=0)
    current_amount: float = Field(ge=0, default=0.0)
    monthly_contribution: float = Field(ge=0)
    deadline_months: int = Field(gt=0)


class GoalOut(GoalCreate):
    id: int
    user_id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── AI Engine Inputs ──────────────────────────────────────────────────────────

class WhatIfScenario(BaseModel):
    description: str = Field(examples=["Buy a ₹50,000 laptop on EMI"])
    monthly_impact: float = Field(description="Additional monthly expense (negative = saving)")
    duration_months: int = Field(gt=0)
    one_time_cost: float = Field(default=0.0, ge=0)


class AllocationRequest(BaseModel):
    monthly_income: Optional[float] = None  # override user's income if provided


class SimulationRequest(BaseModel):
    scenarios: List[WhatIfScenario]
    projection_months: int = Field(default=12, ge=1, le=60)


class GoalPredictionRequest(BaseModel):
    goal_id: int


class DebtOptimizationRequest(BaseModel):
    strategy: str = Field(default="avalanche", pattern="^(avalanche|snowball)$")
