"""Utility helpers shared by clinic extraction modules."""

from __future__ import annotations

import re
from typing import Optional


ADDRESS_HINT_WORDS = {
    "rd",
    "road",
    "st",
    "street",
    "ave",
    "avenue",
    "hwy",
    "highway",
    "ln",
    "lane",
    "ct",
    "court",
    "dr",
    "drive",
}
STATE_ABBREVIATIONS = {
    "qld",
    "nsw",
    "vic",
    "sa",
    "wa",
    "tas",
    "nt",
    "act",
}

SERVICE_MARKER_PHRASES = (
    "assist with",
    "services include",
    "we can help with",
    "we offer the following services",
    "our services include",
)

GENERIC_PHONE_DIGITS = {
    # Main national contact number that should be ignored for clinic-specific
    # phone extraction.
    "1800366837",
}


def normalize_whitespace(value: str) -> str:
    """Collapse repeated whitespace and strip leading/trailing spaces."""
    return " ".join(value.split())


def looks_like_address(text: str) -> bool:
    """Heuristic to decide whether *text* looks like a street address."""
    text = normalize_whitespace(text)
    if not text:
        return False
    lower = text.lower()
    has_digit = any(ch.isdigit() for ch in lower)
    if not has_digit:
        return False

    tokens = re.split(r"[\s,]+", lower)
    if any(token in ADDRESS_HINT_WORDS for token in tokens):
        return True
    if any(token in STATE_ABBREVIATIONS for token in tokens):
        return True
    return False


def extract_email_from_href(href: str) -> Optional[str]:
    """Extract a plain email address from a mailto: link."""
    if not href.lower().startswith("mailto:"):
        return None
    email = href.split(":", 1)[1]
    email = email.split("?", 1)[0]
    email = email.strip()
    return email or None


def phone_digits(text: str) -> str:
    """Return only the digit characters from a phone string."""
    return re.sub(r"\D", "", text)


def is_generic_phone_number(text: str) -> bool:
    """Return True if *text* looks like a generic (non-clinic) phone number."""
    digits = phone_digits(text)
    return digits in GENERIC_PHONE_DIGITS
