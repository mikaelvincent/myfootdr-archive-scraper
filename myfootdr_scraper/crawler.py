"""Crawler for discovering archived /our-clinics/ URLs."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from heapq import heappop, heappush
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
    extract_wayback_timestamp,
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


def _enqueue(
    queue: list[tuple[int, str]],
    queued_canonical: Set[str],
    visited_canonical: Set[str],
    url: str,
) -> None:
    """Add *url* to the priority queue if it has not already been seen.

    URLs are prioritised by their Wayback timestamp so that newer captures are processed before older ones. This helps
    avoid inefficient loops over many historical snapshots of the same page.
    """
    canon = canonicalize_wayback_url(url)
    if canon in visited_canonical or canon in queued_canonical:
        return

    timestamp = extract_wayback_timestamp(url) or 0
    # Use a negative timestamp so that the most recent captures (largest
    # timestamp) are popped first from the min-heap.
    priority = -timestamp
    heappush(queue, (priority, url))
    queued_canonical.add(canon)


def crawl_our_clinics(
    start_url: str,
    *,
    session: Optional[requests.Session] = None,
    limit: Optional[int] = None,
) -> CrawlerResult:
    """Crawl from ``start_url`` over archived /our-clinics/ pages.

    Only Wayback URLs whose original location lies under
    ``https://www.myfootdr.com.au/our-clinics/`` are visited. When multiple
    Wayback captures of the same content are linked, newer captures are
    prioritised by the crawler to minimise redundant work.
    """
    if session is None:
        from .http_client import create_session

        session = create_session()

    # Priority queue of ``(priority, url)`` where *priority* is derived from
    # the negative Wayback timestamp so that newer captures are processed
    # first.
    queue: list[tuple[int, str]] = []
    visited_canonical: Set[str] = set()
    queued_canonical: Set[str] = set()

    _enqueue(queue, queued_canonical, visited_canonical, start_url)

    discovered_original: Set[str] = set()
    clinic_candidates: Set[str] = set()
    clinics_by_key: Dict[Tuple[str, str], Tuple[Clinic, int]] = {}
    visited_pages = 0

    while queue:
        _, current = heappop(queue)
        canon_current = canonicalize_wayback_url(current)
        if canon_current in visited_canonical:
            continue
        visited_canonical.add(canon_current)
        queued_canonical.discard(canon_current)

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
            timestamp = extract_wayback_timestamp(current) or 0
            existing = clinics_by_key.get(key)
            if existing is None:
                clinics_by_key[key] = (clinic, timestamp)
            else:
                existing_clinic, existing_timestamp = existing
                new_score = clinic.non_empty_field_count()
                existing_score = existing_clinic.non_empty_field_count()
                if new_score > existing_score or (
                    new_score == existing_score and timestamp > existing_timestamp
                ):
                    clinics_by_key[key] = (clinic, timestamp)

        for link in soup.find_all("a", href=True):
            href = link["href"]
            absolute = urljoin(current, href)
            if not is_in_scope_wayback_url(absolute):
                continue
            _enqueue(queue, queued_canonical, visited_canonical, absolute)

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
        clinics=tuple(clinic for clinic, _ in clinics_by_key.values()),
    )
