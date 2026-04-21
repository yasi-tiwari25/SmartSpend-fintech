"""
Transaction Auto-Categorizer
Uses TF-IDF style keyword scoring + pattern matching to automatically
classify Indian transaction descriptions into categories.

No external ML libraries needed — works with pure Python.
Designed for Indian payment descriptions (UPI, banks, apps).
"""

import re
from typing import Dict, List, Tuple


# =============================================================================
# Keyword Training Data
# Each category has keywords with confidence weights (0.0 - 1.0)
# Higher weight = stronger signal for that category
# =============================================================================

CATEGORY_KEYWORDS: Dict[str, Dict[str, float]] = {

    "dining": {
        # Food delivery apps
        "swiggy": 1.0, "zomato": 1.0, "dunzo": 0.9, "eatsure": 0.9,
        "faasos": 0.9, "box8": 0.9, "freshmenu": 0.9, "rebel foods": 0.9,
        # Restaurants & cafes
        "restaurant": 0.9, "cafe": 0.8, "coffee": 0.7, "pizza": 0.9,
        "burger": 0.9, "biryani": 0.9, "hotel": 0.6, "dhaba": 0.9,
        "canteen": 0.8, "mess": 0.8, "food": 0.6, "eat": 0.5,
        "dining": 1.0, "lunch": 0.8, "dinner": 0.8, "breakfast": 0.8,
        "mcdonalds": 1.0, "kfc": 1.0, "dominos": 1.0, "subway": 1.0,
        "ccd": 0.9, "starbucks": 1.0, "chai": 0.7, "tea": 0.6,
        "haldirams": 0.9, "barbeque": 0.9, "bbq": 0.9,
    },

    "groceries": {
        # Grocery apps
        "bigbasket": 1.0, "blinkit": 1.0, "grofers": 1.0, "zepto": 1.0,
        "jiomart": 0.9, "milkbasket": 0.9, "country delight": 0.9,
        # Stores
        "dmart": 1.0, "reliance fresh": 1.0, "more supermarket": 0.9,
        "star bazaar": 0.9, "spencer": 0.9, "natures basket": 0.9,
        "supermarket": 0.9, "hypermarket": 0.9, "grocery": 1.0,
        "vegetables": 0.9, "fruits": 0.8, "milk": 0.7, "provisions": 0.9,
        "kirana": 1.0, "sabzi": 0.9, "mandi": 0.8, "ration": 0.8,
    },

    "shopping": {
        # E-commerce
        "amazon": 0.8, "flipkart": 1.0, "myntra": 1.0, "ajio": 1.0,
        "nykaa": 1.0, "meesho": 1.0, "snapdeal": 1.0, "shopsy": 1.0,
        "tatacliq": 1.0, "jiomart": 0.7, "firstcry": 0.9,
        # Physical retail
        "mall": 0.8, "shopping": 0.9, "retail": 0.8, "store": 0.6,
        "clothes": 0.9, "clothing": 0.9, "fashion": 0.9, "shoes": 0.9,
        "footwear": 0.9, "accessories": 0.8, "jewellery": 0.9,
        "electronics": 0.8, "gadget": 0.8, "appliance": 0.8,
        "westside": 0.9, "zara": 0.9, "h&m": 0.9, "max fashion": 0.9,
        "pantaloons": 0.9, "lifestyle": 0.8, "shoppers stop": 0.9,
    },

    "transport": {
        # Ride apps
        "uber": 1.0, "ola": 1.0, "rapido": 1.0, "bluemart": 0.8,
        "meru": 0.9, "savaari": 0.9,
        # Public transport
        "metro": 0.9, "bus": 0.7, "auto": 0.7, "rickshaw": 0.8,
        "irctc": 1.0, "train": 0.8, "railway": 0.9, "flight": 0.9,
        "indigo": 0.9, "air india": 0.9, "spicejet": 0.9, "akasa": 0.9,
        "makemytrip": 0.8, "goibibo": 0.8, "redbus": 0.9,
        # Fuel
        "petrol": 1.0, "diesel": 1.0, "fuel": 1.0, "hp": 0.6,
        "indian oil": 0.9, "bharat petroleum": 0.9, "iocl": 0.9,
        "fasttag": 0.9, "toll": 0.8, "parking": 0.8,
    },

    "utilities": {
        # Electricity
        "bescom": 1.0, "msedcl": 1.0, "tata power": 0.9, "adani electricity": 0.9,
        "electricity": 1.0, "electric": 0.9, "power bill": 1.0,
        # Water & Gas
        "water": 0.8, "bwssb": 1.0, "gas": 0.7, "lpg": 1.0,
        "indane": 0.9, "hp gas": 0.9, "bharat gas": 0.9,
        # Internet & Phone
        "jio": 0.8, "airtel": 0.8, "vi ": 0.8, "vodafone": 0.8, "bsnl": 0.9,
        "broadband": 0.9, "internet": 0.8, "wifi": 0.8, "recharge": 0.7,
        "postpaid": 0.9, "prepaid": 0.7, "mobile bill": 0.9,
        # Other utilities
        "utility": 1.0, "bill payment": 0.8, "maintenance": 0.7,
    },

    "rent": {
        "rent": 1.0, "rental": 1.0, "house rent": 1.0, "flat rent": 1.0,
        "pg": 0.8, "paying guest": 0.9, "accommodation": 0.8,
        "landlord": 1.0, "owner": 0.6, "lease": 0.9, "tenancy": 0.9,
        "society": 0.7, "maintenance charges": 0.8, "hoa": 0.8,
    },

    "emi": {
        "emi": 1.0, "loan": 0.9, "mortgage": 1.0, "home loan": 1.0,
        "car loan": 1.0, "personal loan": 1.0, "education loan": 1.0,
        "hdfc loan": 1.0, "sbi loan": 1.0, "icici loan": 1.0,
        "bajaj finance": 0.9, "emi payment": 1.0, "installment": 0.9,
        "repayment": 0.9, "equated": 1.0, "nach": 0.8, "auto debit loan": 0.9,
    },

    "insurance": {
        "insurance": 1.0, "lic": 1.0, "premium": 0.8, "policy": 0.7,
        "hdfc life": 0.9, "icici prudential": 0.9, "sbi life": 0.9,
        "bajaj allianz": 0.9, "star health": 0.9, "mediclaim": 1.0,
        "term plan": 0.9, "ulip": 0.9, "endowment": 0.9,
        "health insurance": 1.0, "car insurance": 1.0, "bike insurance": 1.0,
        "general insurance": 0.9, "new india": 0.8,
        "premium payment": 1.0, "lic premium": 1.0, "insurance premium": 1.0,
    },

    "healthcare": {
        "hospital": 1.0, "clinic": 0.9, "doctor": 0.9, "pharmacy": 1.0,
        "medicine": 1.0, "medical": 0.9, "pharma": 0.9, "apollo": 0.8,
        "netmeds": 1.0, "1mg": 1.0, "pharmeasy": 1.0, "medplus": 1.0,
        "lab": 0.8, "diagnostic": 0.9, "pathology": 0.9, "xray": 0.9,
        "scan": 0.7, "consultation": 0.8, "dentist": 0.9, "dental": 0.9,
        "physiotherapy": 0.9, "ayurveda": 0.8, "chemist": 0.9,
    },

    "education": {
        "school": 0.9, "college": 0.9, "university": 0.9, "institute": 0.7,
        "fees": 0.7, "tuition": 0.9, "coaching": 0.9, "course": 0.8,
        "udemy": 1.0, "coursera": 1.0, "unacademy": 1.0, "byju": 1.0,
        "vedantu": 1.0, "upgrad": 1.0, "simplilearn": 1.0,
        "books": 0.8, "stationery": 0.8, "exam": 0.7, "test": 0.5,
        "library": 0.8, "workshop": 0.7, "seminar": 0.7,
    },

    "entertainment": {
        # Streaming
        "netflix": 1.0, "prime video": 1.0, "hotstar": 1.0, "disney": 0.9,
        "sony liv": 1.0, "zee5": 1.0, "jiocinema": 1.0, "mxplayer": 0.9,
        "youtube premium": 1.0, "spotify": 1.0, "gaana": 0.9, "wynk": 0.9,
        # Entertainment venues
        "movie": 0.9, "cinema": 1.0, "pvr": 1.0, "inox": 1.0, "cinepolis": 1.0,
        "bookmyshow": 1.0, "concert": 0.9, "event": 0.7, "show": 0.6,
        "game": 0.7, "gaming": 0.8, "steam": 0.9, "playstation": 0.9,
        "amusement": 0.9, "park": 0.6, "zoo": 0.9, "museum": 0.9,
        "subscription": 0.7, "streaming": 0.9,
    },

    "savings": {
        "fd": 0.9, "fixed deposit": 1.0, "recurring deposit": 1.0, "rd": 0.8,
        "ppf": 1.0, "nps": 1.0, "savings": 0.8, "deposit": 0.7,
        "piggybank": 0.9, "jar": 0.8, "jupiter": 0.7, "fi money": 0.8,
        "transfer to savings": 1.0, "sweep": 0.8,
    },

    "investment": {
        "mutual fund": 1.0, "sip": 1.0, "stocks": 1.0, "shares": 0.9,
        "zerodha": 1.0, "groww": 1.0, "upstox": 1.0, "angel broking": 0.9,
        "paytm money": 0.9, "icicidirect": 0.9, "hdfc securities": 0.9,
        "demat": 0.9, "nifty": 0.8, "sensex": 0.8, "equity": 0.8,
        "gold": 0.7, "sovereign gold bond": 1.0, "sgb": 1.0,
        "crypto": 0.9, "bitcoin": 0.9, "wazirx": 1.0, "coinswitch": 1.0,
    },

    "salary": {
        "salary": 1.0, "sal credit": 1.0, "sal cr": 1.0,
        "payroll": 1.0, "wages": 0.9, "stipend": 0.9,
        "employer": 0.8, "company credit": 0.7, "neft credit": 0.5,
        "income": 0.6, "credited by": 0.5,
    },

    "freelance": {
        "freelance": 1.0, "client payment": 0.9, "project payment": 0.9,
        "invoice": 0.8, "consulting": 0.8, "contract": 0.7,
        "upwork": 1.0, "fiverr": 1.0, "toptal": 1.0, "payment received": 0.6,
    },

    "other": {},  # fallback
}


# =============================================================================
# Classifier
# =============================================================================

def classify(description: str) -> Dict:
    """
    Classify a transaction description into a category.

    Returns:
        {
            "category": "dining",
            "confidence": 0.95,
            "confidence_label": "High",
            "all_scores": {"dining": 0.95, "groceries": 0.1, ...}
        }
    """
    text = _preprocess(description)
    scores = _score_all_categories(text)

    # Sort by score
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_category, top_score = sorted_scores[0]

    # If score too low, fall back to "other"
    if top_score < 0.15:
        top_category = "other"
        top_score = 1.0

    return {
        "category": top_category,
        "confidence": round(top_score, 3),
        "confidence_label": _confidence_label(top_score),
        "top_3": [
            {"category": cat, "score": round(score, 3)}
            for cat, score in sorted_scores[:3]
            if score > 0
        ],
    }


def batch_classify(descriptions: List[str]) -> List[Dict]:
    """Classify multiple descriptions at once."""
    return [classify(d) for d in descriptions]


# =============================================================================
# Internal Helpers
# =============================================================================

def _preprocess(text: str) -> str:
    """Lowercase, remove special chars, normalize spaces."""
    text = text.lower()
    text = re.sub(r'[₹\$\*\#\@\!\&\(\)\[\]\{\}]', ' ', text)
    text = re.sub(r'\d+', ' ', text)  # remove numbers
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _score_all_categories(text: str) -> Dict[str, float]:
    """Score text against all categories using keyword matching."""
    scores = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        if not keywords:
            scores[category] = 0.0
            continue

        category_score = 0.0
        matched_keywords = []

        for keyword, weight in keywords.items():
            # Exact word/phrase match
            if keyword in text:
                category_score += weight
                matched_keywords.append(keyword)

        # Normalize by number of matches to avoid bias toward keyword-rich categories
        if matched_keywords:
            # Boost for multiple matches (more evidence = more confident)
            boost = min(1.0 + (len(matched_keywords) - 1) * 0.1, 1.5)
            category_score = (category_score / len(matched_keywords)) * boost

        scores[category] = round(category_score, 4)

    # Normalize all scores to 0-1 range
    max_score = max(scores.values()) if scores else 1.0
    if max_score > 0:
        scores = {k: round(v / max_score, 4) for k, v in scores.items()}

    return scores


def _confidence_label(score: float) -> str:
    if score >= 0.85:
        return "High"
    elif score >= 0.60:
        return "Medium"
    elif score >= 0.30:
        return "Low"
    else:
        return "Very Low"


# =============================================================================
# Quick Test (run this file directly to test)
# =============================================================================

if __name__ == "__main__":
    test_cases = [
        ("Swiggy order biryani", "dining"),
        ("BESCOM electricity bill", "utilities"),
        ("Amazon order shoes", "shopping"),
        ("Uber ride to office", "transport"),
        ("Netflix subscription", "entertainment"),
        ("HDFC home loan EMI", "emi"),
        ("BigBasket vegetables", "groceries"),
        ("Zerodha SIP mutual fund", "investment"),
        ("Apollo pharmacy medicines", "healthcare"),
        ("Salary credit from TCS", "salary"),
        ("Udemy Python course", "education"),
        ("LIC premium payment", "insurance"),
        ("House rent payment", "rent"),
        ("Groww FD fixed deposit", "savings"),
    ]

    print("=" * 60)
    print("Transaction Auto-Categorizer Test")
    print("=" * 60)

    correct = 0
    for description, expected in test_cases:
        result = classify(description)
        predicted = result["category"]
        confidence = result["confidence_label"]
        is_correct = predicted == expected
        if is_correct:
            correct += 1
        status = "✅" if is_correct else "❌"
        print(f"{status} '{description}'")
        print(f"   Predicted: {predicted} ({confidence}) | Expected: {expected}")

    print()
    print(f"Accuracy: {correct}/{len(test_cases)} = {correct/len(test_cases)*100:.0f}%")