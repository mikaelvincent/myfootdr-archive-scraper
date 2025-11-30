"""Field-level extraction helpers for clinic pages."""

from __future__ import annotations

from typing import List, Optional

from bs4 import BeautifulSoup

from .utils import (
    SERVICE_MARKER_PHRASES,
    extract_email_from_href,
    is_generic_phone_number,
    looks_like_address,
    normalize_whitespace,
)


def _clean_heading(text: str) -> str:
    """Normalise heading text and strip common boilerplate prefixes."""
    cleaned = normalize_whitespace(text)
    lower = cleaned.lower()
    prefixes = ("welcome to ", "welcome back to ")
    for prefix in prefixes:
        if lower.startswith(prefix):
            return cleaned[len(prefix) :].lstrip()
    return cleaned


def extract_clinic_name(soup: BeautifulSoup) -> Optional[str]:
    """Extract the clinic name from the page, if possible."""
    # 1. Main content H1 heading.
    selectors = [
        "main h1",
        "article h1",
        ".entry-content h1",
        ".site-main h1",
        "h1",
    ]
    for selector in selectors:
        heading = soup.select_one(selector)
        if heading:
            text = heading.get_text(" ", strip=True)
            if not text:
                continue
            cleaned = _clean_heading(text)
            if cleaned and cleaned.lower() not in {"our clinics", "clinics"}:
                return cleaned

    # 2. Last breadcrumb item.
    crumb_selectors = [
        ".breadcrumbs li:last-child",
        ".breadcrumb li:last-child",
        'nav[aria-label*="breadcrumb"] li:last-child',
    ]
    for selector in crumb_selectors:
        crumb = soup.select_one(selector)
        if crumb:
            text = crumb.get_text(" ", strip=True)
            cleaned = normalize_whitespace(text)
            if cleaned and cleaned.lower() not in {"our clinics", "clinics"}:
                return cleaned

    # 3. Fallback to <title>.
    if soup.title and soup.title.string:
        title = normalize_whitespace(soup.title.string)
        # Strip common separators like " - " or " | ".
        for sep in (" - ", " | ", " – "):
            if sep in title:
                title = title.split(sep)[0]
                break
        cleaned = _clean_heading(title)
        if cleaned:
            return cleaned

    return None


def extract_address(soup: BeautifulSoup) -> Optional[str]:
    """Extract the clinic's street address, if present."""
    # 1. Anchors in main content that look like addresses.
    anchor_selectors = [
        "main a",
        "article a",
        ".entry-content a",
    ]
    for selector in anchor_selectors:
        for anchor in soup.select(selector):
            text = anchor.get_text(" ", strip=True)
            if not text:
                continue
            text = normalize_whitespace(text)
            if looks_like_address(text):
                return text

    # 2. Fallback: any text node in main content that looks like an address.
    container_selectors = [
        "main",
        "article",
        ".entry-content",
    ]
    for selector in container_selectors:
        container = soup.select_one(selector)
        if not container:
            continue
        for element in container.find_all(["p", "div", "span"]):
            text = element.get_text(" ", strip=True)
            text = normalize_whitespace(text)
            if looks_like_address(text):
                return text

    return None


def extract_email(soup: BeautifulSoup) -> Optional[str]:
    """Extract the primary clinic email address, if present."""
    selectors = [
        'main a[href^="mailto:"]',
        'article a[href^="mailto:"]',
        '.entry-content a[href^="mailto:"]',
        'a[href^="mailto:"]',
    ]
    seen = set()
    for selector in selectors:
        for anchor in soup.select(selector):
            href = anchor.get("href")
            if not href:
                continue
            email = extract_email_from_href(href)
            if not email:
                continue
            if email in seen:
                continue
            seen.add(email)
            return email
    return None


def extract_phone(soup: BeautifulSoup) -> Optional[str]:
    """Extract a clinic-specific phone number.

    Prefers local clinic numbers and ignores known generic contact numbers.
    """
    selectors = [
        'main a[href^="tel:"]',
        'article a[href^="tel:"]',
        '.entry-content a[href^="tel:"]',
        'a[href^="tel:"]',
    ]
    candidates: List[str] = []

    for selector in selectors:
        for anchor in soup.select(selector):
            text = anchor.get_text(strip=True)
            if not text:
                href = anchor.get("href", "")
                text = href.split(":", 1)[1] if ":" in href else href
            if not text:
                continue
            text = normalize_whitespace(text)
            candidates.append(text)

    # Filter out known generic numbers.
    clinic_candidates = [c for c in candidates if not is_generic_phone_number(c)]

    if clinic_candidates:
        return clinic_candidates[0]
    if candidates:
        # Fall back to the first number even if it might be generic.
        return candidates[0]

    return None


def extract_services(soup: BeautifulSoup) -> List[str]:
    """Extract a list of services described on the clinic page."""
    services: List[str] = []

    # 1. Look for a marker phrase and take the following <ul>.
    main_containers = soup.select("main, article, .entry-content")
    for container in main_containers:
        for node in container.find_all(string=True):
            lower = node.strip().lower()
            if not lower:
                continue
            if any(phrase in lower for phrase in SERVICE_MARKER_PHRASES):
                ul = node.find_next("ul")
                if not ul:
                    continue
                for li in ul.find_all("li"):
                    text = li.get_text(" ", strip=True)
                    text = normalize_whitespace(text)
                    if text:
                        services.append(text)
                if services:
                    return services

    # 2. Fallback: choose the first "reasonable" UL in main content.
    ul_candidates = soup.select("main ul, article ul, .entry-content ul")
    for ul in ul_candidates:
        items: List[str] = []
        for li in ul.find_all("li"):
            text = li.get_text(" ", strip=True)
            text = normalize_whitespace(text)
            if not text:
                continue
            if len(text) > 120:
                # Probably not a simple "services" list.
                items = []
                break
            items.append(text)
        if items:
            services = items
            break

    return services
