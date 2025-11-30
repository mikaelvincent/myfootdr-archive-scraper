"""Clinic page detection heuristics."""

from __future__ import annotations

from bs4 import BeautifulSoup

from .fields import extract_address, extract_clinic_name, extract_phone


def is_clinic_page(soup: BeautifulSoup) -> bool:
    """Return True if the page *soup* looks like a clinic detail page.

    The heuristic is intentionally simple:

    * We attempt to extract the clinic name, address, and phone number.
    * If at least two of these three fields are present, we treat the page
      as a clinic page.
    * As a small safety net, we also accept pages whose main heading starts
      with "Welcome to", which matches many clinic pages.
    """
    name = extract_clinic_name(soup)
    address = extract_address(soup)
    phone = extract_phone(soup)

    score = sum(1 for value in (name, address, phone) if value)
    if score >= 2:
        return True

    heading = soup.find("h1")
    if heading:
        text = heading.get_text(" ", strip=True).lower()
        if text.startswith("welcome to "):
            return True

    return False
