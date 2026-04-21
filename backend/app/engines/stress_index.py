"""
Engine 3: Financial Stress Index (Upgraded with Isolation Forest)

Hybrid approach:
- Isolation Forest (ML) for anomaly detection on monthly spending patterns
- Statistical signals for interpretable breakdowns
- Combines both for final FSI score
"""

import numpy as np
from collections import defaultdict
from typing import List, Dict, Any
from datetime import datetime

from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


# =========================
# Constants
# =========================

DISCRETIONARY = {"dining", "entertainment", "shopping"}
ESSENTIAL = {"groceries", "utilities", "rent", "transport", "healthcare"}
EMI_CATS = {"emi"}

SAFE_COVERAGE = 0.85
SAFE_EMI_RATIO = 0.35
SAFE_VOLATILITY = 0.25
SAFE_DISCRETIONARY_GROWTH = 0.20
SAFE_TREND_GROWTH = 0.05

# Isolation Forest contamination — assumes ~15% of months might be anomalous
IF_CONTAMINATION = 0.15


# =========================
# Main Entry
# =========================

def run(
    monthly_income: float,
    transactions: list,
    total_emi: float,
) -> Dict[str, Any]:

    if not transactions:
        return _empty_response()

    # ── Group transactions by month ──
    monthly = _group_by_month(transactions)

    if len(monthly) < 2:
        return _insufficient_data_response()

    months_sorted = sorted(monthly.keys())
    expense_totals = [monthly[m]["total_expense"] for m in months_sorted]
    discretionary_totals = [monthly[m]["discretionary"] for m in months_sorted]

    # ── Statistical Signals ──
    signals = []
    signal_score = 0

    # Signal 1: Expense Volatility
    vol_score, vol_signal = _check_volatility(expense_totals)
    signal_score += vol_score * 25
    if vol_signal:
        signals.append(vol_signal)

    # Signal 2: Discretionary Spike
    disc_score, disc_signal = _check_discretionary_growth(discretionary_totals)
    signal_score += disc_score * 20
    if disc_signal:
        signals.append(disc_signal)

    # Signal 3: Income Coverage
    last_expense = expense_totals[-1]
    cov_score, cov_signal = _check_coverage(last_expense, monthly_income)
    signal_score += cov_score * 25
    if cov_signal:
        signals.append(cov_signal)

    # Signal 4: EMI Burden
    emi_score, emi_signal = _check_emi_burden(total_emi, monthly_income)
    signal_score += emi_score * 20
    if emi_signal:
        signals.append(emi_signal)

    # Signal 5: Rising Trend
    trend_score, trend_signal = _check_trend(expense_totals)
    signal_score += trend_score * 10
    if trend_signal:
        signals.append(trend_signal)

    statistical_fsi = min(100, round(signal_score, 2))

    # ── Isolation Forest (ML) Anomaly Detection ──
    if_score, if_signals, anomaly_months = _run_isolation_forest(
        monthly, months_sorted, monthly_income, total_emi
    )

    # Add anomaly signals
    signals.extend(if_signals)

    # ── Hybrid FSI Score ──
    # 60% statistical (interpretable) + 40% ML (personalized anomaly detection)
    if len(monthly) >= 4:
        fsi = round(0.60 * statistical_fsi + 0.40 * if_score, 2)
    else:
        # Not enough data for reliable IF — rely more on stats
        fsi = round(0.80 * statistical_fsi + 0.20 * if_score, 2)

    fsi = min(100, max(0, fsi))

    label, color = _classify(fsi)
    coverage_ratio = round((last_expense / monthly_income) * 100, 2) if monthly_income else 0
    emi_burden_pct = round((total_emi / monthly_income) * 100, 2) if monthly_income else 0

    trend_data = [
        {"month": m, "total": round(monthly[m]["total_expense"], 2)}
        for m in months_sorted
    ]

    return {
        "financial_stress_index": fsi,
        "label": label,
        "color": color,
        "signals": signals,
        "monthly_expense_trend": trend_data,
        "coverage_ratio": coverage_ratio,
        "emi_burden_pct": emi_burden_pct,
        "anomaly_months": anomaly_months,
        "ml_anomaly_score": round(if_score, 2),
        "statistical_score": statistical_fsi,
        "interpretation": _interpret(fsi, label),
        "method": "Isolation Forest (ML) + Statistical Signals (Hybrid)",
    }


# =========================
# Isolation Forest Engine
# =========================

def _run_isolation_forest(
    monthly: dict,
    months_sorted: list,
    monthly_income: float,
    total_emi: float,
) -> tuple:
    """
    Trains Isolation Forest on user's own monthly financial features.
    Detects which months are anomalous compared to the user's own baseline.
    """

    # Build feature matrix — one row per month
    feature_matrix = []
    for m in months_sorted:
        data = monthly[m]
        row = [
            data["total_expense"],
            data["discretionary"],
            data["essentials"],
            data["total_expense"] / monthly_income if monthly_income else 0,
            data["discretionary"] / data["total_expense"] if data["total_expense"] else 0,
        ]
        feature_matrix.append(row)

    X = np.array(feature_matrix)

    # Need at least 3 months for meaningful anomaly detection
    if len(X) < 3:
        return 0, [], []

    # Normalize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Isolation Forest on user's own data
    contamination = min(IF_CONTAMINATION, (len(X) - 1) / len(X))
    clf = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
    )
    clf.fit(X_scaled)

    # Predict anomaly scores (-1 = anomaly, 1 = normal)
    predictions = clf.predict(X_scaled)
    scores = clf.decision_function(X_scaled)  # lower = more anomalous

    # Normalize anomaly score to 0-100
    # decision_function returns negative values for anomalies
    min_score = scores.min()
    max_score = scores.max()
    if max_score != min_score:
        normalized = 1 - (scores - min_score) / (max_score - min_score)
    else:
        normalized = np.zeros(len(scores))

    # Overall IF stress score = weighted average (recent months matter more)
    weights = np.linspace(0.5, 1.0, len(normalized))
    if_stress_score = float(np.average(normalized, weights=weights)) * 100

    # Identify anomalous months
    anomaly_months = []
    if_signals = []

    for i, (month, pred, norm_score) in enumerate(zip(months_sorted, predictions, normalized)):
        if pred == -1:  # anomaly detected
            anomaly_months.append(month)
            if_signals.append({
                "type": "ml_anomaly_detected",
                "severity": "high" if norm_score > 0.7 else "medium",
                "message": f"Isolation Forest detected abnormal spending pattern in {month}. "
                           f"This month's behavior significantly deviates from your personal baseline.",
            })

    return if_stress_score, if_signals, anomaly_months


# =========================
# Statistical Signal Checks
# =========================

def _check_volatility(expense_totals):
    mean = np.mean(expense_totals)
    std = np.std(expense_totals)
    cv = std / mean if mean else 0
    if cv > SAFE_VOLATILITY:
        score = min(1.0, cv / 0.5)
        return score, {
            "type": "high_volatility",
            "severity": "high" if cv > 0.4 else "medium",
            "message": f"Expense volatility is {round(cv * 100)}% — spending is highly inconsistent month to month.",
        }
    return cv / SAFE_VOLATILITY * 0.3, None


def _check_discretionary_growth(disc_totals):
    if len(disc_totals) < 2:
        return 0, None
    growth = (disc_totals[-1] - disc_totals[0]) / disc_totals[0] if disc_totals[0] else 0
    if growth > SAFE_DISCRETIONARY_GROWTH:
        score = min(1.0, growth / 0.5)
        return score, {
            "type": "discretionary_spike",
            "severity": "high" if growth > 0.4 else "medium",
            "message": f"Discretionary spending grew {round(growth * 100)}% — dining, shopping, entertainment increasing fast.",
        }
    return 0, None


def _check_coverage(last_expense, income):
    if not income:
        return 0, None
    ratio = last_expense / income
    if ratio > SAFE_COVERAGE:
        score = min(1.0, (ratio - SAFE_COVERAGE) / 0.15)
        return score, {
            "type": "low_coverage",
            "severity": "high" if ratio > 1.0 else "medium",
            "message": f"Last month's expenses consumed {round(ratio * 100)}% of income — very little left for savings.",
        }
    return 0, None


def _check_emi_burden(total_emi, income):
    if not income:
        return 0, None
    ratio = total_emi / income
    if ratio > SAFE_EMI_RATIO:
        score = min(1.0, (ratio - SAFE_EMI_RATIO) / 0.15)
        return score, {
            "type": "high_emi_burden",
            "severity": "high" if ratio > 0.5 else "medium",
            "message": f"EMIs consume {round(ratio * 100)}% of income — above the safe 35% threshold.",
        }
    return ratio / SAFE_EMI_RATIO * 0.3, None


def _check_trend(expense_totals):
    if len(expense_totals) < 2:
        return 0, None
    x = np.arange(len(expense_totals))
    slope, _ = np.polyfit(x, expense_totals, 1)
    mean = np.mean(expense_totals)
    growth_rate = slope / mean if mean else 0
    if growth_rate > SAFE_TREND_GROWTH:
        score = min(1.0, growth_rate / 0.15)
        return score, {
            "type": "rising_expense_trend",
            "severity": "high" if growth_rate > 0.1 else "medium",
            "message": f"Expenses are growing at {round(growth_rate * 100, 1)}% per month — outpacing safe limits.",
        }
    return 0, None


# =========================
# Grouping Helper
# =========================

def _group_by_month(transactions):
    monthly = defaultdict(lambda: {
        "total_expense": 0,
        "total_income": 0,
        "discretionary": 0,
        "essentials": 0,
        "emi": 0,
    })

    for t in transactions:
        date = t.date or datetime.utcnow()
        month_key = date.strftime("%Y-%m")
        cat = (t.category or "other").lower()

        if t.type == "expense":
            monthly[month_key]["total_expense"] += t.amount
            if cat in DISCRETIONARY:
                monthly[month_key]["discretionary"] += t.amount
            elif cat in ESSENTIAL:
                monthly[month_key]["essentials"] += t.amount
            elif cat in EMI_CATS:
                monthly[month_key]["emi"] += t.amount
        else:
            monthly[month_key]["total_income"] += t.amount

    return monthly


# =========================
# Classification
# =========================

def _classify(fsi):
    if fsi < 20:
        return "Low", "green"
    elif fsi < 40:
        return "Moderate", "yellow"
    elif fsi < 65:
        return "Elevated", "orange"
    else:
        return "High", "red"


def _interpret(fsi, label):
    messages = {
        "Low": "Your finances look healthy. Keep maintaining these habits.",
        "Moderate": "Some stress indicators detected. Review flagged signals and adjust spending.",
        "Elevated": "Multiple stress signals active. Consider cutting discretionary spending.",
        "High": "High financial stress detected. Immediate action recommended — review budget urgently.",
    }
    return messages.get(label, "")


def _empty_response():
    return {
        "financial_stress_index": 0,
        "label": "Insufficient Data",
        "color": "gray",
        "signals": [],
        "monthly_expense_trend": [],
        "coverage_ratio": 0,
        "emi_burden_pct": 0,
        "anomaly_months": [],
        "ml_anomaly_score": 0,
        "statistical_score": 0,
        "interpretation": "Add transactions to compute your stress index.",
        "method": "Isolation Forest (ML) + Statistical Signals (Hybrid)",
    }


def _insufficient_data_response():
    return {
        "financial_stress_index": 0,
        "label": "Insufficient Data",
        "color": "gray",
        "signals": [],
        "monthly_expense_trend": [],
        "coverage_ratio": 0,
        "emi_burden_pct": 0,
        "anomaly_months": [],
        "ml_anomaly_score": 0,
        "statistical_score": 0,
        "interpretation": "Add at least 2 months of transactions to compute your stress index.",
        "method": "Isolation Forest (ML) + Statistical Signals (Hybrid)",
    }