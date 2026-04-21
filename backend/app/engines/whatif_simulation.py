"""
Engine 2: What-If Simulation Engine
Simulates how a hypothetical financial decision impacts future cash flow and balance.
Uses month-by-month projection with compounding savings growth.
"""
'''
import numpy as np
from typing import List, Dict, Any
from app.schemas.schemas import WhatIfScenario


SAVINGS_ANNUAL_RETURN = 0.065  # assumed 6.5% p.a. on savings (FD/liquid fund)
MONTHLY_RETURN = (1 + SAVINGS_ANNUAL_RETURN) ** (1 / 12) - 1


def run(
    monthly_income: float,
    current_monthly_expenses: float,
    current_balance: float,
    scenarios: List[WhatIfScenario],
    projection_months: int = 12,
) -> Dict[str, Any]:
    """
    Projects two timelines:
    - Baseline: no change to current spending
    - With scenario(s): impact of the proposed decisions
    Returns month-by-month balance comparison and key metrics.
    """

    baseline = _project_baseline(
        monthly_income, current_monthly_expenses, current_balance, projection_months
    )

    scenario_results = []
    combined_monthly_impact = sum(s.monthly_impact for s in scenarios)
    combined_one_time = sum(s.one_time_cost for s in scenarios)

    scenario_projection = _project_with_scenarios(
        monthly_income,
        current_monthly_expenses,
        current_balance,
        scenarios,
        projection_months,
    )

    balance_delta = [
        round(scenario_projection["balances"][i] - baseline["balances"][i], 2)
        for i in range(projection_months)
    ]

    breakeven_month = None
    for i, delta in enumerate(balance_delta):
        if delta >= 0:
            breakeven_month = i + 1
            break

    scenario_results = []
    for s in scenarios:
        scenario_results.append({
            "description": s.description,
            "monthly_impact": s.monthly_impact,
            "one_time_cost": s.one_time_cost,
            "duration_months": s.duration_months,
            "total_cost": round(s.one_time_cost + s.monthly_impact * s.duration_months, 2),
        })

    verdict = _generate_verdict(
        baseline["final_balance"],
        scenario_projection["final_balance"],
        combined_one_time,
        combined_monthly_impact,
        monthly_income,
        breakeven_month,
    )

    return {
        "projection_months": projection_months,
        "baseline": {
            "monthly_savings": round(baseline["monthly_savings"], 2),
            "final_balance": round(baseline["final_balance"], 2),
            "balances": [round(b, 2) for b in baseline["balances"]],
        },
        "with_scenarios": {
            "monthly_savings": round(scenario_projection["monthly_savings"], 2),
            "final_balance": round(scenario_projection["final_balance"], 2),
            "balances": [round(b, 2) for b in scenario_projection["balances"]],
            "one_time_cost": round(combined_one_time, 2),
        },
        "balance_delta": balance_delta,
        "breakeven_month": breakeven_month,
        "scenarios": scenario_results,
        "verdict": verdict,
    }


def _project_baseline(income, expenses, balance, months) -> Dict:
    monthly_savings = income - expenses
    balances = []
    current = balance
    for _ in range(months):
        current = current * (1 + MONTHLY_RETURN) + monthly_savings
        balances.append(current)
    return {"monthly_savings": monthly_savings, "final_balance": balances[-1], "balances": balances}


def _project_with_scenarios(income, expenses, balance, scenarios, months) -> Dict:
    current = balance - sum(s.one_time_cost for s in scenarios)
    balances = []
    for month in range(1, months + 1):
        active_impact = sum(
            s.monthly_impact for s in scenarios if month <= s.duration_months
        )
        monthly_savings = income - expenses - active_impact
        current = current * (1 + MONTHLY_RETURN) + monthly_savings
        balances.append(current)

    base_savings = income - expenses
    avg_impact = sum(s.monthly_impact for s in scenarios) / len(scenarios) if scenarios else 0
    return {
        "monthly_savings": base_savings - avg_impact,
        "final_balance": balances[-1],
        "balances": balances,
    }


def _generate_verdict(baseline_final, scenario_final, one_time, monthly_impact, income, breakeven) -> Dict:
    loss = round(baseline_final - scenario_final, 2)
    affordable = monthly_impact < income * 0.1 and one_time < income * 2

    if scenario_final < 0:
        rating = "high_risk"
        summary = "This decision could push your balance negative. Not recommended."
    elif loss > income * 3:
        rating = "caution"
        summary = "Significant financial impact. Proceed carefully."
    elif affordable:
        rating = "safe"
        summary = "This decision appears financially manageable."
    else:
        rating = "moderate_risk"
        summary = "This will strain your budget. Consider delaying or reducing scope."

    return {
        "rating": rating,
        "summary": summary,
        "total_wealth_impact": -loss,
        "breakeven_month": breakeven,
    }
'''
"""
Engine 2: What-If Simulation Engine (Upgraded with Monte Carlo)

Simulates how a hypothetical financial decision impacts future cash flow and balance.
Includes:
- Deterministic baseline projection
- Scenario-based projection
- Breakeven detection
- Risk verdict
- Monte Carlo probabilistic simulation
"""

import numpy as np
from typing import List, Dict, Any
from app.schemas.schemas import WhatIfScenario


# =========================
# Assumptions
# =========================

SAVINGS_ANNUAL_RETURN = 0.065  # 6.5% annual assumed savings return
MONTHLY_RETURN = (1 + SAVINGS_ANNUAL_RETURN) ** (1 / 12) - 1

MC_SIMULATIONS = 500          # number of Monte Carlo runs
MC_STD_DEV = 0.03             # annual return volatility (3%)


# =========================
# Main Entry Function
# =========================

def run(
    monthly_income: float,
    current_monthly_expenses: float,
    current_balance: float,
    scenarios: List[WhatIfScenario],
    projection_months: int = 12,
) -> Dict[str, Any]:

    # ---------- Baseline Projection ----------
    baseline = _project_baseline(
        monthly_income,
        current_monthly_expenses,
        current_balance,
        projection_months,
    )

    # ---------- Scenario Projection ----------
    scenario_projection = _project_with_scenarios(
        monthly_income,
        current_monthly_expenses,
        current_balance,
        scenarios,
        projection_months,
    )

    # ---------- Month-by-Month Delta ----------
    balance_delta = [
        round(
            scenario_projection["balances"][i] - baseline["balances"][i],
            2,
        )
        for i in range(projection_months)
    ]

    # ---------- Breakeven Detection ----------
    breakeven_month = None
    for i, delta in enumerate(balance_delta):
        if delta >= 0:
            breakeven_month = i + 1
            break

    # ---------- Scenario Summary ----------
    scenario_results = []
    for s in scenarios:
        scenario_results.append({
            "description": s.description,
            "monthly_impact": s.monthly_impact,
            "one_time_cost": s.one_time_cost,
            "duration_months": s.duration_months,
            "total_cost": round(
                s.one_time_cost + s.monthly_impact * s.duration_months,
                2,
            ),
        })

    # ---------- Monte Carlo Simulation ----------
    mc_results = _monte_carlo_projection(
        monthly_income,
        current_monthly_expenses,
        current_balance,
        scenarios,
        projection_months,
    )

    # Probability of outperforming deterministic baseline
    mc_results["probability_outperform_baseline"] = round(
        np.mean(
            np.array(mc_results["all_final_balances"])
            > baseline["final_balance"]
        ) * 100,
        2,
    )

    # Remove raw simulation list from API response
    mc_results.pop("all_final_balances")

    # ---------- Verdict ----------
    combined_one_time = sum(s.one_time_cost for s in scenarios)
    combined_monthly = sum(s.monthly_impact for s in scenarios)

    verdict = _generate_verdict(
        baseline["final_balance"],
        scenario_projection["final_balance"],
        combined_one_time,
        combined_monthly,
        monthly_income,
        breakeven_month,
    )

    return {
        "projection_months": projection_months,
        "baseline": baseline,
        "with_scenarios": scenario_projection,
        "balance_delta": balance_delta,
        "breakeven_month": breakeven_month,
        "scenarios": scenario_results,
        "verdict": verdict,
        "monte_carlo": mc_results,
    }


# =========================
# Deterministic Baseline
# =========================

def _project_baseline(income, expenses, balance, months) -> Dict:
    monthly_savings = income - expenses
    balances = []
    current = balance

    for _ in range(months):
        current = current * (1 + MONTHLY_RETURN) + monthly_savings
        balances.append(current)

    return {
        "monthly_savings": round(monthly_savings, 2),
        "final_balance": round(balances[-1], 2),
        "balances": [round(b, 2) for b in balances],
    }


# =========================
# Deterministic Scenario Projection
# =========================

def _project_with_scenarios(income, expenses, balance, scenarios, months) -> Dict:
    current = balance - sum(s.one_time_cost for s in scenarios)
    balances = []

    for month in range(1, months + 1):

        active_impact = sum(
            s.monthly_impact
            for s in scenarios
            if month <= s.duration_months
        )

        monthly_savings = income - expenses - active_impact
        current = current * (1 + MONTHLY_RETURN) + monthly_savings
        balances.append(current)

    avg_impact = (
        sum(s.monthly_impact for s in scenarios) / len(scenarios)
        if scenarios else 0
    )

    return {
        "monthly_savings": round((income - expenses - avg_impact), 2),
        "final_balance": round(balances[-1], 2),
        "balances": [round(b, 2) for b in balances],
        "one_time_cost": round(sum(s.one_time_cost for s in scenarios), 2),
    }


# =========================
# Monte Carlo Simulation
# =========================

def _monte_carlo_projection(
    income,
    expenses,
    balance,
    scenarios,
    months,
    simulations=MC_SIMULATIONS,
):

    final_balances = []

    for _ in range(simulations):
        current = balance - sum(s.one_time_cost for s in scenarios)

        for month in range(1, months + 1):

            # Random annual return
            annual_return = np.random.normal(
                SAVINGS_ANNUAL_RETURN,
                MC_STD_DEV,
            )

            monthly_return = (1 + annual_return) ** (1 / 12) - 1

            active_impact = sum(
                s.monthly_impact
                for s in scenarios
                if month <= s.duration_months
            )

            monthly_savings = income - expenses - active_impact

            current = current * (1 + monthly_return) + monthly_savings

        final_balances.append(current)

    final_balances = np.array(final_balances)

    return {
        "median_final_balance": round(np.median(final_balances), 2),
        "p10_balance": round(np.percentile(final_balances, 10), 2),
        "p90_balance": round(np.percentile(final_balances, 90), 2),
        "probability_negative_balance": round(
            np.mean(final_balances < 0) * 100,
            2,
        ),
        "all_final_balances": final_balances.tolist(),
    }


# =========================
# Verdict Engine
# =========================

def _generate_verdict(
    baseline_final,
    scenario_final,
    one_time,
    monthly_impact,
    income,
    breakeven,
) -> Dict:

    loss = round(baseline_final - scenario_final, 2)
    affordable = monthly_impact < income * 0.1 and one_time < income * 2

    if scenario_final < 0:
        rating = "high_risk"
        summary = "This decision could push your balance negative."
    elif loss > income * 3:
        rating = "caution"
        summary = "Significant long-term financial impact."
    elif affordable:
        rating = "safe"
        summary = "This decision appears financially manageable."
    else:
        rating = "moderate_risk"
        summary = "This may strain your monthly budget."

    return {
        "rating": rating,
        "summary": summary,
        "total_wealth_impact": -loss,
        "breakeven_month": breakeven,
    }
