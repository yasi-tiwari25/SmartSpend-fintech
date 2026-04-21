"""
Engine 5: Lifestyle Inflation Detector (v2)
Uses Isolation Forest (anomaly detection) + % of income tracking
for more accurate, spike-aware inflation detection.

Isolation Forest: detects which categories are spending anomalously
                  compared to the user's own history (unsupervised).
% Change vs Income: gives a clean, explainable growth signal per category.

Combined score weights both signals for a robust final result.
"""

import numpy as np
from typing import List, Dict, Any
from collections import defaultdict
from app.models.models import Transaction, TransactionCategory

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

LIFESTYLE_CATEGORIES = [
    TransactionCategory.dining,
    TransactionCategory.entertainment,
    TransactionCategory.shopping,
    TransactionCategory.transport,
]

SAFE_GROWTH_RATE = 0.03        # 3% monthly growth = normal
INCOME_RATIO_THRESHOLD = 0.40  # >40% of income on discretionary = warning
IF_CONTAMINATION = 0.2         # expect ~20% of months to be anomalous


def run(
    monthly_income: float,
    income_growth_rate: float,
    transactions: List[Transaction],
) -> Dict[str, Any]:
    """
    Detects lifestyle inflation using:
    1. Isolation Forest — flags anomalous spending months per category
    2. % change vs income growth — measures sustained trend
    Returns per-category signals + overall inflation score.
    """

    if not transactions:
        return _empty_result()

    monthly_by_cat = _group_by_month_and_category(transactions)
    months = sorted(monthly_by_cat.keys())

    if len(months) < 2:
        return _empty_result()

    category_analysis = {}
    inflation_flags = []
    combined_scores = []

    for cat in LIFESTYLE_CATEGORIES:
        monthly_vals = [monthly_by_cat[m].get(cat, 0.0) for m in months]
        nonzero = [v for v in monthly_vals if v > 0]

        if len(nonzero) < 2:
            continue

        avg_spend = float(np.mean(nonzero))
        std_spend = float(np.std(nonzero)) if len(nonzero) > 1 else 0.0

        # ── Signal 1: Isolation Forest anomaly detection ──────────────────
        anomaly_months = []
        anomaly_score_norm = 0.0

        if SKLEARN_AVAILABLE and len(monthly_vals) >= 4:
            X = np.array(monthly_vals).reshape(-1, 1)
            contamination = min(0.45, max(0.05, IF_CONTAMINATION))
            iso = IsolationForest(
                contamination=contamination,
                random_state=42,
                n_estimators=100,
            )
            preds = iso.fit_predict(X)          # -1 = anomaly, 1 = normal
            scores = iso.decision_function(X)   # lower = more anomalous

            anomaly_indices = [i for i, p in enumerate(preds) if p == -1]
            anomaly_months = [months[i] for i in anomaly_indices]

            # Normalize: fraction of months flagged as anomalous
            anomaly_score_norm = len(anomaly_indices) / len(monthly_vals)

            # Extra weight if recent months are anomalous
            recent_anomalous = sum(1 for i in anomaly_indices if i >= len(months) - 2)
            if recent_anomalous > 0:
                anomaly_score_norm = min(1.0, anomaly_score_norm + 0.2)
        else:
            # Fallback: z-score based anomaly detection (no sklearn needed)
            if std_spend > 0:
                z_scores = [(v - avg_spend) / std_spend for v in monthly_vals]
                anomaly_indices = [i for i, z in enumerate(z_scores) if z > 1.5]
                anomaly_months = [months[i] for i in anomaly_indices]
                anomaly_score_norm = min(1.0, len(anomaly_indices) / max(len(monthly_vals), 1))

        # ── Signal 2: % change vs income growth ───────────────────────────
        # Compare first half vs second half average spend
        mid = len(monthly_vals) // 2
        first_half_avg = float(np.mean(monthly_vals[:mid])) if mid > 0 else avg_spend
        second_half_avg = float(np.mean(monthly_vals[mid:])) if mid < len(monthly_vals) else avg_spend

        pct_change = ((second_half_avg - first_half_avg) / (first_half_avg + 1e-9)) * 100
        income_growth_pct = income_growth_rate * 100 * len(months)
        inflation_vs_income = pct_change - income_growth_pct

        # % of income this category consumes
        income_share_pct = (avg_spend / (monthly_income + 1e-9)) * 100

        # ── Combined score (0–100) ─────────────────────────────────────────
        # Weight: 50% anomaly signal + 50% % growth signal
        growth_score = min(100, max(0, inflation_vs_income * 2))
        anomaly_score = anomaly_score_norm * 100
        combined = round(0.5 * growth_score + 0.5 * anomaly_score, 1)
        combined_scores.append(combined)

        is_inflating = bool(combined > 25 or (pct_change > SAFE_GROWTH_RATE * 100 and len(anomaly_months) > 0))

        category_analysis[cat.value] = {
            "monthly_trend": [round(v, 2) for v in monthly_vals],
            "avg_monthly_spend": round(avg_spend, 2),
            "std_deviation": round(std_spend, 2),
            "pct_change_overall": round(pct_change, 1),
            "vs_income_growth": round(inflation_vs_income, 1),
            "income_share_pct": round(income_share_pct, 1),
            "anomalous_months": anomaly_months,
            "anomaly_score": round(anomaly_score_norm * 100, 1),
            "combined_inflation_score": combined,
            "inflating": is_inflating,
            "method": "isolation_forest" if (SKLEARN_AVAILABLE and len(monthly_vals) >= 4) else "z_score_fallback",
        }

        if is_inflating:
            severity = "high" if combined > 60 else "medium" if combined > 30 else "low"
            flag_msg = (
                f"{cat.value.capitalize()} spending grew {pct_change:.1f}% "
                f"({inflation_vs_income:+.1f}% vs income). "
            )
            if anomaly_months:
                flag_msg += f"Anomalous months: {', '.join(anomaly_months[-3:])}."

            inflation_flags.append({
                "category": cat.value,
                "severity": severity,
                "combined_score": combined,
                "pct_change": round(pct_change, 1),
                "anomalous_months_count": len(anomaly_months),
                "message": flag_msg,
                "projected_annual_excess": round(
                    avg_spend * max(0, pct_change / 100) * 12, 2
                ),
            })

    # ── Overall discretionary metrics ─────────────────────────────────────
    all_disc = [
        sum(monthly_by_cat[m].get(c, 0) for c in LIFESTYLE_CATEGORIES)
        for m in months
    ]
    disc_income_ratio = (float(np.mean(all_disc)) / (monthly_income + 1e-9)) * 100
    disc_income_ratio = round(disc_income_ratio, 1)

    inflation_score = round(float(np.mean(combined_scores)), 1) if combined_scores else 0.0
    label = _classify(inflation_score, inflation_flags, disc_income_ratio)

    return {
        "lifestyle_inflation_score": inflation_score,
        "label": label,
        "detection_method": "isolation_forest + pct_change" if SKLEARN_AVAILABLE else "z_score + pct_change",
        "months_analyzed": len(months),
        "discretionary_income_ratio_pct": disc_income_ratio,
        "income_ratio_warning": bool(disc_income_ratio > INCOME_RATIO_THRESHOLD * 100),
        "inflation_flags": sorted(inflation_flags, key=lambda x: -x["combined_score"]),
        "category_breakdown": category_analysis,
        "months": months,
        "summary": _summarize(inflation_score, inflation_flags, disc_income_ratio),
    }


def _group_by_month_and_category(transactions) -> Dict:
    grouped = defaultdict(lambda: defaultdict(float))
    for t in transactions:
        if t.type == "expense" and t.date:
            grouped[t.date.strftime("%Y-%m")][t.category] += t.amount
    return grouped


def _classify(score: float, flags: list, disc_ratio: float) -> str:
    high_flags = [f for f in flags if f["severity"] == "high"]
    if score < 15 and not flags:
        return "Stable 🟢"
    elif score < 30 or (not high_flags and disc_ratio < 35):
        return "Mild Inflation 🟡"
    elif score < 55:
        return "Moderate Inflation 🟠"
    else:
        return "Severe Inflation 🔴"


def _summarize(score: float, flags: list, disc_ratio: float) -> str:
    if not flags:
        return (
            f"No significant lifestyle inflation detected. "
            f"Discretionary spend is {disc_ratio:.1f}% of income — within healthy range."
        )
    cats = ", ".join(f["category"] for f in flags)
    worst = max(flags, key=lambda x: x["combined_score"])
    return (
        f"Lifestyle inflation detected in: {cats}. "
        f"Worst offender: {worst['category']} (score {worst['combined_score']:.0f}/100). "
        f"Discretionary spending is {disc_ratio:.1f}% of income. "
        f"Isolation Forest flagged anomalous spending months — review and cap growth."
    )


def _empty_result():
    return {
        "lifestyle_inflation_score": 0,
        "label": "Insufficient Data",
        "detection_method": "isolation_forest + pct_change",
        "months_analyzed": 0,
        "discretionary_income_ratio_pct": 0,
        "income_ratio_warning": False,
        "inflation_flags": [],
        "category_breakdown": {},
        "months": [],
        "summary": "Add at least 2 months of transaction data to detect lifestyle inflation.",
    }