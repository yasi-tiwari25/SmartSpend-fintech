"""
Engine 1: AI Salary Allocation Engine
Optimizes monthly income distribution across EMIs, bills, savings, and investments.
Uses a rule-based prioritization model with surplus optimization.
"""

from typing import List, Dict
from app.models.models import Transaction, Loan, TransactionCategory


def run(
    monthly_income: float,
    transactions: List[Transaction],
    loans: List[Loan],
) -> Dict:
    """
    Returns a recommended monthly allocation breakdown.
    Priority order: EMIs → Fixed bills → Essentials → Emergency fund → Goals → Discretionary
    """

    # 1. Compute fixed obligatory outflows
    total_emi = sum(l.monthly_emi for l in loans)

    # Identify recurring fixed expenses from last 3 months of transactions
    fixed_categories = {
        TransactionCategory.rent,
        TransactionCategory.utilities,
        TransactionCategory.insurance,
    }
    essential_categories = {
        TransactionCategory.groceries,
        TransactionCategory.healthcare,
        TransactionCategory.transport,
        TransactionCategory.education,
    }

    expenses = [t for t in transactions if t.type == "expense"]

    fixed_expenses = sum(t.amount for t in expenses if t.category in fixed_categories)
    essential_expenses = sum(t.amount for t in expenses if t.category in essential_categories)
    discretionary_expenses = sum(
        t.amount for t in expenses
        if t.category not in fixed_categories
        and t.category not in essential_categories
        and t.category != TransactionCategory.emi
    )

    # 2. Compute surplus
    total_committed = total_emi + fixed_expenses + essential_expenses
    surplus = monthly_income - total_committed

    # 3. Apply 50/30/20 heuristic on surplus, adjusted for debt load
    debt_ratio = total_emi / monthly_income if monthly_income > 0 else 0

    if debt_ratio > 0.4:
        # High debt: prioritize debt repayment over savings
        emergency_fund_pct = 0.05
        savings_pct = 0.10
        investment_pct = 0.05
    elif debt_ratio > 0.2:
        emergency_fund_pct = 0.08
        savings_pct = 0.15
        investment_pct = 0.07
    else:
        emergency_fund_pct = 0.10
        savings_pct = 0.20
        investment_pct = 0.10

    emergency_fund = monthly_income * emergency_fund_pct
    savings = monthly_income * savings_pct
    investments = monthly_income * investment_pct
    discretionary_budget = max(0, surplus - emergency_fund - savings - investments)

    # 4. Health score (0-100)
    health_score = _compute_health_score(
        monthly_income, total_emi, fixed_expenses, essential_expenses, surplus
    )

    return {
        "monthly_income": round(monthly_income, 2),
        "allocation": {
            "emis_and_loans": round(total_emi, 2),
            "fixed_bills": round(fixed_expenses, 2),
            "essentials": round(essential_expenses, 2),
            "emergency_fund": round(emergency_fund, 2),
            "savings": round(savings, 2),
            "investments": round(investments, 2),
            "discretionary": round(discretionary_budget, 2),
        },
        "surplus_after_commitments": round(surplus, 2),
        "debt_to_income_ratio": round(debt_ratio * 100, 1),
        "health_score": health_score,
        "warnings": _generate_warnings(debt_ratio, surplus, monthly_income),
        "recommendations": _generate_recommendations(
            debt_ratio, surplus, monthly_income, discretionary_expenses, discretionary_budget
        ),
    }


def _compute_health_score(income, emi, fixed, essential, surplus) -> int:
    score = 100
    if income == 0:
        return 0
    # Penalize high EMI burden
    emi_ratio = emi / income
    if emi_ratio > 0.5:
        score -= 35
    elif emi_ratio > 0.35:
        score -= 20
    elif emi_ratio > 0.2:
        score -= 10

    # Penalize negative surplus
    if surplus < 0:
        score -= 30
    elif surplus / income < 0.1:
        score -= 15

    # Penalize if essentials alone consume most income
    if (fixed + essential) / income > 0.7:
        score -= 15

    return max(0, min(100, score))


def _generate_warnings(debt_ratio: float, surplus: float, income: float) -> list:
    warnings = []
    if debt_ratio > 0.5:
        warnings.append("⚠️ EMIs exceed 50% of income — critically high debt burden.")
    elif debt_ratio > 0.35:
        warnings.append("⚠️ EMIs exceed 35% of income — consider debt consolidation.")
    if surplus < 0:
        warnings.append("🚨 Expenses exceed income this month — you are in a deficit.")
    elif surplus / income < 0.1 and income > 0:
        warnings.append("⚠️ Less than 10% income left after fixed costs — very tight budget.")
    return warnings


def _generate_recommendations(debt_ratio, surplus, income, actual_disc, budget_disc) -> list:
    recs = []
    if debt_ratio > 0.35:
        recs.append("Consider prepaying the highest-interest loan to reduce EMI burden faster.")
    if surplus > 0 and surplus / income > 0.3:
        recs.append("You have healthy surplus — consider increasing SIP or goal contributions.")
    if actual_disc > budget_disc * 1.2:
        recs.append(
            f"Discretionary spending is ₹{actual_disc - budget_disc:.0f} over budget — review dining/shopping."
        )
    if not recs:
        recs.append("Your allocation looks balanced. Stay consistent with your savings plan.")
    return recs
