"""
Engine 4: Goal Probability Predictor
Estimates the likelihood of achieving a financial goal using Monte Carlo simulation.
Accounts for income variability, spending trends, and compounding returns.
"""

import numpy as np
from typing import List, Dict, Any
from app.models.models import Transaction, Goal


N_SIMULATIONS = 2000
ANNUAL_RETURN = 0.07       # assumed 7% p.a. for invested savings
INCOME_VOLATILITY = 0.05   # 5% std dev on monthly income (freelance shock)
EXPENSE_VOLATILITY = 0.08  # 8% std dev on monthly expenses


def run(
    goal: Goal,
    monthly_income: float,
    transactions: List[Transaction],
) -> Dict[str, Any]:
    """
    Runs Monte Carlo simulation to compute the probability of reaching goal.
    Returns probability, projected range, and actionable recommendations.
    """
    monthly_return = (1 + ANNUAL_RETURN) ** (1 / 12) - 1

    # Compute average monthly expenses from history
    expenses = [t.amount for t in transactions if t.type == "expense"]
    avg_monthly_expense = (sum(expenses) / max(len(set(
        t.date.strftime("%Y-%m") for t in transactions if t.date
    )), 1)) if expenses else monthly_income * 0.7

    months_left = goal.deadline_months
    target = goal.target_amount
    start = goal.current_amount
    monthly_contrib = goal.monthly_contribution

    final_balances = []
    success_count = 0

    for _ in range(N_SIMULATIONS):
        balance = start
        for _ in range(months_left):
            # Stochastic income and expense
            sim_income = monthly_income * (1 + np.random.normal(0, INCOME_VOLATILITY))
            sim_expense = avg_monthly_expense * (1 + np.random.normal(0, EXPENSE_VOLATILITY))
            sim_contrib = min(monthly_contrib, max(0, sim_income - sim_expense))

            # Compound growth on existing balance + contribution
            balance = balance * (1 + monthly_return) + sim_contrib

        final_balances.append(balance)
        if balance >= target:
            success_count += 1

    probability = round((success_count / N_SIMULATIONS) * 100, 1)
    final_balances_arr = np.array(final_balances)

    # Required monthly contribution to guarantee (95th pct) success
    required_contrib = _compute_required_contrib(
        target, start, months_left, monthly_return, monthly_income, avg_monthly_expense
    )

    shortfall = max(0, target - float(np.median(final_balances_arr)))
    months_to_extend = _months_to_achieve_with_current_contrib(
        target, start, monthly_contrib, monthly_return
    )

    return {
        "goal": {
            "name": goal.name,
            "target_amount": target,
            "current_amount": start,
            "monthly_contribution": monthly_contrib,
            "deadline_months": months_left,
        },
        "probability_pct": probability,
        "confidence_label": _confidence_label(probability),
        "projected_range": {
            "p10": round(float(np.percentile(final_balances_arr, 10)), 2),
            "p50_median": round(float(np.percentile(final_balances_arr, 50)), 2),
            "p90": round(float(np.percentile(final_balances_arr, 90)), 2),
        },
        "expected_shortfall": round(shortfall, 2),
        "required_monthly_contribution": round(required_contrib, 2),
        "months_to_achieve_at_current_rate": months_to_extend,
        "recommendations": _generate_recommendations(
            probability, shortfall, monthly_contrib, required_contrib, months_left
        ),
    }


def _confidence_label(prob: float) -> str:
    if prob >= 85:
        return "On Track 🟢"
    elif prob >= 60:
        return "Likely 🟡"
    elif prob >= 35:
        return "At Risk 🟠"
    else:
        return "Unlikely 🔴"


def _compute_required_contrib(target, start, months, monthly_return, income, avg_expense) -> float:
    """Calculate the fixed monthly contribution needed to reach target with certainty."""
    if monthly_return == 0 or months == 0:
        return max(0, (target - start) / months) if months > 0 else 0
    fv_existing = start * (1 + monthly_return) ** months
    annuity_factor = ((1 + monthly_return) ** months - 1) / monthly_return
    needed = (target - fv_existing) / annuity_factor
    return max(0, needed)


def _months_to_achieve_with_current_contrib(target, start, monthly_contrib, monthly_return) -> int:
    """How many months until goal is reached at current contribution rate."""
    if monthly_contrib <= 0:
        return -1  # Never
    balance = start
    for month in range(1, 601):
        balance = balance * (1 + monthly_return) + monthly_contrib
        if balance >= target:
            return month
    return -1  # Beyond 50 years


def _generate_recommendations(prob, shortfall, current_contrib, required_contrib, months_left) -> list:
    recs = []
    gap = required_contrib - current_contrib
    if prob >= 85:
        recs.append("You're on track! Maintain your current contribution discipline.")
    elif prob >= 60:
        recs.append(f"Increase monthly contribution by ₹{gap:.0f} to improve your odds significantly.")
    else:
        recs.append(f"You need ₹{required_contrib:.0f}/month to meet this goal. Current: ₹{current_contrib:.0f}.")
        if months_left > 6:
            recs.append("Consider extending your deadline or reducing the target amount.")
        recs.append("Look for areas to cut discretionary spending to free up contribution capacity.")
    return recs
