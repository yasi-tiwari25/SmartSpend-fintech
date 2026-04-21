from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List as PyList
from pydantic import BaseModel                    # ← add this
from app.database import get_db
from app.models.models import User, Transaction, Loan, Goal
from app.schemas.schemas import (
    AllocationRequest, SimulationRequest, DebtOptimizationRequest, GoalPredictionRequest
)
from app.services.auth_service import get_current_user
from app.engines import (
    salary_allocation,
    whatif_simulation,
    stress_index,
    goal_predictor,
    lifestyle_inflation,
    debt_optimizer,
    transaction_categorizer,
)


router = APIRouter(prefix="/ai", tags=["AI Engines"])


def _get_user_data(user: User, db: Session):
    """Helper to fetch all user financial data."""
    transactions = db.query(Transaction).filter(Transaction.user_id == user.id).all()
    loans = db.query(Loan).filter(Loan.user_id == user.id).all()
    goals = db.query(Goal).filter(Goal.user_id == user.id).all()
    return transactions, loans, goals


# ── Engine 1: Salary Allocation ───────────────────────────────────────────────

@router.post("/salary-allocation")
def salary_allocation_endpoint(
    payload: AllocationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Returns an optimized monthly income allocation plan.
    Breaks down how salary should be distributed across EMIs, bills,
    savings, investments, and discretionary spending.
    """
    transactions, loans, _ = _get_user_data(user, db)
    income = payload.monthly_income or user.monthly_income
    if not income:
        raise HTTPException(400, "Monthly income not set. Update your profile or pass monthly_income.")
    return salary_allocation.run(income, transactions, loans)


# ── Engine 2: What-If Simulation ─────────────────────────────────────────────

@router.post("/what-if-simulation")
def whatif_simulation_endpoint(
    payload: SimulationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Simulates the financial impact of one or more hypothetical decisions.
    Returns a month-by-month balance comparison with baseline vs. scenario projection.
    """
    transactions, loans, _ = _get_user_data(user, db)

    income = user.monthly_income
    expenses = [t for t in transactions if t.type == "expense"]
    monthly_expenses = sum(t.amount for t in expenses)

    # Normalize to monthly average based on available months
    months_with_data = len(set(
        t.date.strftime("%Y-%m") for t in expenses if t.date
    )) or 1
    avg_monthly_expenses = monthly_expenses / months_with_data

    total_emi = sum(l.monthly_emi for l in loans)
    current_balance = income - avg_monthly_expenses  # rough approximation

    return whatif_simulation.run(
        income,
        avg_monthly_expenses + total_emi,
        current_balance * 3,  # assume 3 months buffer as starting balance
        payload.scenarios,
        payload.projection_months,
    )


# ── Engine 3: Financial Stress Index ─────────────────────────────────────────

@router.get("/stress-index")
def stress_index_endpoint(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Computes the Financial Stress Index (0-100) based on spending patterns,
    income coverage, EMI burden, and month-over-month expense volatility.
    """
    transactions, loans, _ = _get_user_data(user, db)
    total_emi = sum(l.monthly_emi for l in loans)
    return stress_index.run(user.monthly_income, transactions, total_emi)


# ── Engine 4: Goal Probability Predictor ─────────────────────────────────────

@router.post("/goal-probability")
def goal_probability_endpoint(
    payload: GoalPredictionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Runs a Monte Carlo simulation (2000 trials) to estimate the probability
    of achieving a specific financial goal given current income and spending trends.
    """
    transactions, _, goals = _get_user_data(user, db)
    goal = db.query(Goal).filter(Goal.id == payload.goal_id, Goal.user_id == user.id).first()
    if not goal:
        raise HTTPException(404, "Goal not found.")
    return goal_predictor.run(goal, user.monthly_income, transactions)


# ── Engine 5: Lifestyle Inflation Detector ───────────────────────────────────

@router.get("/lifestyle-inflation")
def lifestyle_inflation_endpoint(
    income_growth_rate: float = 0.01,  # default 1% monthly income growth
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Detects lifestyle inflation by analyzing discretionary spending growth
    relative to income growth. Flags categories with unsustainable growth.
    """
    transactions, _, _ = _get_user_data(user, db)
    return lifestyle_inflation.run(user.monthly_income, income_growth_rate, transactions)


# ── Engine 6: Debt Optimization Planner ─────────────────────────────────────

@router.post("/debt-optimization")
def debt_optimization_endpoint(
    payload: DebtOptimizationRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Compares Avalanche vs Snowball debt repayment strategies.
    Returns a month-by-month payoff schedule, total interest saved,
    and recommended payoff order.
    """
    transactions, loans, _ = _get_user_data(user, db)
    if not loans:
        raise HTTPException(404, "No loans found. Add your loans first.")

    expenses = [t for t in transactions if t.type == "expense"]
    months_with_data = len(set(
        t.date.strftime("%Y-%m") for t in expenses if t.date
    )) or 1
    avg_monthly_expenses = sum(t.amount for t in expenses) / months_with_data
    monthly_surplus = user.monthly_income - avg_monthly_expenses

    return debt_optimizer.run(loans, monthly_surplus, payload.strategy)

# ── Engine 7: Transaction Auto-Categorizer ────────────────────────────────────

class CategorizeRequest(BaseModel):
    description: str

class BatchCategorizeRequest(BaseModel):
    descriptions: PyList[str]


@router.post("/categorize-transaction")
def categorize_transaction(payload: CategorizeRequest):
    """
    Automatically categorizes a transaction description.
    e.g. "Swiggy order" → dining, "BESCOM bill" → utilities
    """
    return transaction_categorizer.classify(payload.description)


@router.post("/categorize-transactions-batch")
def categorize_transactions_batch(payload: BatchCategorizeRequest):
    """
    Categorize multiple transaction descriptions at once.
    """
    results = transaction_categorizer.batch_classify(payload.descriptions)
    return {"results": results, "count": len(results)}
