"""URL parsing and normalisation helpers for Wayback / My Foot Dr."""

from __future__ import annotations

import re
from typing import Optional
from urllib.parse import urlsplit, urlunsplit

WAYBACK_URL_RE = re.compile(r"^https?://web\.archive\.org/web/([^/]+)/(.+)$")
OUR_CLINICS_PREFIX = "https://www.myfootdr.com.au/our-clinics/"


def is_wayback_url(url: str) -> bool:
    """Return True if *url* looks like a Wayback Machine capture URL."""
    return bool(WAYBACK_URL_RE.match(url))


def extract_original_url(wayback_url: str) -> Optional[str]:
    """Extract the original URL from a Wayback capture URL.

    Returns None if *wayback_url* is not a recognised Wayback URL.
    """
    match = WAYBACK_URL_RE.match(wayback_url)
    if not match:
        return None
    return match.group(2)


def _canonicalize_url(url: str) -> str:
    """Canonicalise a URL for de-duplication.

    Normalises scheme and hostname to lower case, removes any query parameters and fragment, and strips a trailing slash
    from the path.
    """
    parts = urlsplit(url)
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, "", ""))


def canonicalize_wayback_url(url: str) -> str:
    """Canonicalise a Wayback URL for de-duplication."""
    return _canonicalize_url(url)


def is_our_clinics_original_url(original_url: str) -> bool:
    """Return True if *original_url* lies under /our-clinics/ on the live site."""
    if original_url.startswith("http://"):
        original_url = "https://" + original_url[len("http://") :]
    return original_url.startswith(OUR_CLINICS_PREFIX)


def canonicalize_original_url(original_url: str) -> str:
    """Canonicalise an original My FootDr URL for comparison."""
    if original_url.startswith("http://"):
        original_url = "https://" + original_url[len("http://") :]
    return _canonicalize_url(original_url)


def is_in_scope_wayback_url(url: str) -> bool:
    """Return True if *url* is a Wayback capture of an /our-clinics/ page."""
    if not is_wayback_url(url):
        return False
    original = extract_original_url(url)
    if original is None:
        return False
    return is_our_clinics_original_url(original)


def is_probable_clinic_url(original_url: str) -> bool:
    """Heuristic to decide whether an original URL is a clinic page.

    For Sprint 2 we treat URLs with a path depth of at least three segments under /our-clinics/ as clinic candidates,
    e.g.:

    /our-clinics/sunshine-coast/noosa/

    This distinguishes them from the landing page and region index pages.
    """
    from urllib.parse import urlsplit as _urlsplit

    canonical = canonicalize_original_url(original_url)
    parts = _urlsplit(canonical)
    segments = [segment for segment in parts.path.split("/") if segment]
    if not segments:
        return False
    if segments[0] != "our-clinics":
        return False
    # Depth >= 3 => /our-clinics/<region>/<clinic>/ or deeper.
    return len(segments) >= 3
