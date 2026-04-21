"""
Engine 6: Debt Optimization Planner
Recommends the most efficient debt repayment strategy.
Supports Avalanche (highest interest first) and Snowball (lowest balance first).
"""

import math
from typing import List, Dict, Any
from app.models.models import Loan


def run(
    loans: List[Loan],
    monthly_surplus: float,
    strategy: str = "avalanche",
) -> Dict[str, Any]:
    """
    Computes an optimized repayment schedule.

    Avalanche: Pay minimums on all, put extra toward highest-interest loan.
               Minimizes total interest paid.
    Snowball:  Pay minimums on all, put extra toward smallest balance loan.
               Maximizes psychological wins (faster payoffs).
    """
    if not loans:
        return {"error": "No loans found to optimize."}

    # Minimum payment = EMI for each loan
    total_emi = sum(l.monthly_emi for l in loans)
    extra = max(0, monthly_surplus - total_emi)

    avalanche_result = _simulate(loans, extra, "avalanche")
    snowball_result = _simulate(loans, extra, "snowball")

    # Pick recommended strategy
    if strategy == "avalanche":
        primary = avalanche_result
        secondary = snowball_result
    else:
        primary = snowball_result
        secondary = avalanche_result

    interest_saved = avalanche_result["total_interest"] - snowball_result["total_interest"]

    return {
        "strategy": strategy,
        "monthly_surplus_available": round(monthly_surplus, 2),
        "total_monthly_emi": round(total_emi, 2),
        "extra_monthly_payment": round(extra, 2),
        "recommended_plan": primary,
        "alternative_plan": secondary,
        "avalanche_vs_snowball": {
            "interest_saved_with_avalanche": round(interest_saved, 2),
            "months_saved_with_avalanche": avalanche_result["total_months"] - snowball_result["total_months"],
            "recommendation": (
                "Avalanche saves more money overall."
                if interest_saved > 0
                else "Both strategies are equivalent for your loan profile."
            ),
        },
        "loan_payoff_order": primary["payoff_order"],
        "tips": _generate_tips(loans, extra, monthly_surplus),
    }


def _simulate(loans: List[Loan], extra: float, strategy: str) -> Dict:
    # Deep copy loan state
    loan_states = [
        {
            "id": l.id,
            "name": l.name,
            "outstanding": l.outstanding,
            "interest_rate": l.interest_rate / 100 / 12,  # monthly
            "emi": l.monthly_emi,
            "paid_off_month": None,
        }
        for l in loans
    ]

    total_interest = 0.0
    month = 0
    payoff_order = []
    schedule = []

    while any(l["outstanding"] > 0.01 for l in loan_states) and month < 600:
        month += 1

        # Sort active loans by strategy priority
        active = [l for l in loan_states if l["outstanding"] > 0.01]
        if strategy == "avalanche":
            priority_loan = max(active, key=lambda l: l["interest_rate"])
        else:
            priority_loan = min(active, key=lambda l: l["outstanding"])

        month_interest = 0.0
        month_payment = 0.0
        extra_remaining = extra

        for loan in loan_states:
            if loan["outstanding"] <= 0.01:
                continue
            interest_charge = loan["outstanding"] * loan["interest_rate"]
            month_interest += interest_charge
            total_interest += interest_charge

            payment = min(loan["emi"], loan["outstanding"] + interest_charge)

            # Apply extra to priority loan
            if loan is priority_loan and extra_remaining > 0:
                extra_payment = min(extra_remaining, loan["outstanding"] + interest_charge - payment)
                payment += extra_payment
                extra_remaining -= extra_payment

            loan["outstanding"] = max(0, loan["outstanding"] + interest_charge - payment)
            month_payment += payment

            if loan["outstanding"] <= 0.01 and loan["paid_off_month"] is None:
                loan["paid_off_month"] = month
                payoff_order.append({
                    "name": loan["name"],
                    "paid_off_in_months": month,
                    "interest_paid": round(interest_charge, 2),  # approximate
                })

        if month <= 24:  # Return first 2 years of schedule
            schedule.append({
                "month": month,
                "total_payment": round(month_payment, 2),
                "interest": round(month_interest, 2),
                "principal": round(month_payment - month_interest, 2),
            })

    return {
        "strategy": strategy,
        "total_months": month,
        "total_interest": round(total_interest, 2),
        "payoff_order": payoff_order,
        "first_24_months_schedule": schedule,
    }


def _generate_tips(loans: List[Loan], extra: float, surplus: float) -> list:
    tips = []
    highest_rate = max(loans, key=lambda l: l.interest_rate)
    if highest_rate.interest_rate > 15:
        tips.append(
            f"'{highest_rate.name}' has a {highest_rate.interest_rate:.1f}% interest rate — "
            f"focus extra payments here first to minimize long-term cost."
        )
    if extra < 500:
        tips.append(
            "Extra payment capacity is low. Even ₹500-₹1000 extra/month can shave months off your debt."
        )
    if len(loans) > 3:
        tips.append("Consider debt consolidation — multiple loans make tracking harder and rates may be negotiable.")
    if surplus > sum(l.monthly_emi for l in loans) * 0.5:
        tips.append("You have healthy surplus. Aggressively prepaying now compounds your savings significantly.")
    return tips
