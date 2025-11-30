"""Crawler for discovering archived /our-clinics/ URLs."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Dict, Optional, Set, Tuple
from urllib.parse import urljoin

import requests

from .clinic_extraction import extract_clinic_from_soup
from .clinic_models import Clinic
from .html_utils import parse_html
from .http_client import HttpRequestError, fetch_html
from .urls import (
    canonicalize_original_url,
    canonicalize_wayback_url,
    extract_original_url,
    is_in_scope_wayback_url,
    is_probable_clinic_url,
)

LOG = logging.getLogger(__name__)


@dataclass
class CrawlerResult:
    """Summary of a crawl run."""

    visited_pages: int
    visited_urls: Set[str]
    discovered_original_urls: Set[str]
    clinic_candidate_original_urls: Set[str]
    clinics: Tuple[Clinic, ...]


def crawl_our_clinics(
    start_url: str,
    *,
    session: Optional[requests.Session] = None,
    limit: Optional[int] = None,
) -> CrawlerResult:
    """Breadth-first crawl from ``start_url`` over archived /our-clinics/ pages.

    Only Wayback URLs whose original location lies under
    ``https://www.myfootdr.com.au/our-clinics/`` are visited.
    """
    if session is None:
        from .http_client import create_session

        session = create_session()

    queue: deque[str] = deque([start_url])
    visited_canonical: Set[str] = set()
    discovered_original: Set[str] = set()
    clinic_candidates: Set[str] = set()
    clinics_by_key: Dict[Tuple[str, str], Clinic] = {}
    visited_pages = 0

    while queue:
        current = queue.popleft()
        canon_current = canonicalize_wayback_url(current)
        if canon_current in visited_canonical:
            continue
        visited_canonical.add(canon_current)

        if not is_in_scope_wayback_url(current):
            LOG.debug("Skipping out-of-scope URL %s", current)
            continue

        original = extract_original_url(current)
        if original is None:
            continue

        canonical_original = canonicalize_original_url(original)
        discovered_original.add(canonical_original)

        if is_probable_clinic_url(canonical_original):
            clinic_candidates.add(canonical_original)

        if limit is not None and visited_pages >= limit:
            LOG.info("Reached crawl limit of %d pages; stopping.", limit)
            break

        visited_pages += 1

        try:
            html = fetch_html(current, session=session)
        except HttpRequestError as exc:
            LOG.warning("Failed to fetch %s: %s", current, exc)
            continue

        soup = parse_html(html)

        # Attempt clinic detection and extraction for every visited page.
        clinic = extract_clinic_from_soup(soup, canonical_original)
        if clinic is not None:
            key = clinic.dedup_key()
            existing = clinics_by_key.get(key)
            if (
                existing is None
                or clinic.non_empty_field_count() > existing.non_empty_field_count()
            ):
                clinics_by_key[key] = clinic

        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute = urljoin(current, href)
            if not is_in_scope_wayback_url(absolute):
                continue
            canon_link = canonicalize_wayback_url(absolute)
            if canon_link in visited_canonical:
                continue
            queue.append(absolute)

    LOG.info(
        "Visited %d pages; discovered %d in-scope URLs (%d clinic candidates, %d clinics extracted).",
        visited_pages,
        len(discovered_original),
        len(clinic_candidates),
        len(clinics_by_key),
    )

    return CrawlerResult(
        visited_pages=visited_pages,
        visited_urls=visited_canonical,
        discovered_original_urls=discovered_original,
        clinic_candidate_original_urls=clinic_candidates,
        clinics=tuple(clinics_by_key.values()),
    )
