"""Crawler for discovering archived /our-clinics/ URLs."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin

import requests

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
    visited_urls: set[str]
    discovered_original_urls: set[str]
    clinic_candidate_original_urls: set[str]


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

    queue = deque([start_url])
    visited_canonical: set[str] = set()
    discovered_original: set[str] = set()
    clinic_candidates: set[str] = set()
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
        "Visited %d pages; discovered %d in-scope URLs (%d clinic candidates).",
        visited_pages,
        len(discovered_original),
        len(clinic_candidates),
    )

    return CrawlerResult(
        visited_pages=visited_pages,
        visited_urls=visited_canonical,
        discovered_original_urls=discovered_original,
        clinic_candidate_original_urls=clinic_candidates,
    )
