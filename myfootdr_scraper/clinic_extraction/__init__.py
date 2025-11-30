"""High-level helpers for extracting clinic data from HTML."""

from __future__ import annotations

from bs4 import BeautifulSoup

from ..html_utils import parse_html
from ..clinic_models import Clinic
from .fields import (
    extract_address,
    extract_clinic_name,
    extract_email,
    extract_phone,
    extract_services,
)
from .detection import is_clinic_page

__all__ = [
    "Clinic",
    "extract_clinic_from_html",
    "extract_clinic_from_soup",
    "extract_clinic_name",
    "extract_address",
    "extract_email",
    "extract_phone",
    "extract_services",
    "is_clinic_page",
]


def extract_clinic_from_soup(soup: BeautifulSoup, original_url: str) -> Clinic | None:
    """Detect and extract clinic data from a parsed BeautifulSoup document.

    Returns a Clinic instance if the page looks like a clinic page, otherwise returns None.
    """
    if not is_clinic_page(soup):
        return None

    name = extract_clinic_name(soup)
    address = extract_address(soup)
    email = extract_email(soup)
    phone = extract_phone(soup)
    services = extract_services(soup)

    # If none of the fields could be extracted, treat this as a non-clinic.
    if not any([name, address, email, phone, services]):
        return None

    return Clinic(
        original_url=original_url,
        name=name,
        address=address,
        email=email,
        phone=phone,
        services=services,
    )


def extract_clinic_from_html(html: str, original_url: str) -> Clinic | None:
    """Parse *html* and attempt to extract a clinic record."""
    soup = parse_html(html)
    return extract_clinic_from_soup(soup, original_url)
