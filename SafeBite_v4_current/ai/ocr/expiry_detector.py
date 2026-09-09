"""Lightweight expiry-date parser used before wiring a production OCR engine."""
import re
from datetime import datetime

DATE_PATTERNS = [
    r"\b(\d{2})[/-](\d{2})[/-](\d{4})\b",
    r"\b(\d{2})[.-](\d{2})[.-](\d{4})\b",
]


def extract_expiry_date(text: str):
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text)
        if match:
            day, month, year = map(int, match.groups())
            try:
                return datetime(year, month, day).date()
            except ValueError:
                return None
    return None


def classify_expiry(expiry_date, today=None):
    if expiry_date is None:
        return "UNKNOWN"
    today = today or datetime.utcnow().date()
    days = (expiry_date - today).days
    if days < 0:
        return "EXPIRED"
    if days <= 7:
        return "NEAR_EXPIRY"
    return "SAFE"
