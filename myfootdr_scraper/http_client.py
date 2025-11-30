"""Simple HTTP client with basic headers, error handling, and retries."""

from __future__ import annotations

import logging
from typing import Optional

import requests

from .config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_USER_AGENT,
)

LOG = logging.getLogger(__name__)


class HttpRequestError(RuntimeError):
    """Raised when a URL cannot be fetched successfully."""


def create_session(user_agent: str = DEFAULT_USER_AGENT) -> requests.Session:
    """Create a configured requests session for scraping.

    A custom User-Agent and sensible Accept headers are applied so that requests to the Wayback Machine look like a
    normal browser.
    """
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": user_agent,
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;" "q=0.9,*/*;q=0.8"
            ),
            "Accept-Language": "en-AU,en;q=0.9",
        }
    )
    return session


def fetch_html(
    url: str,
    session: Optional[requests.Session] = None,
    timeout: float = DEFAULT_REQUEST_TIMEOUT,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> str:
    """Fetch a URL and return its HTML as text.

    Retries on network errors and non-2xx status codes up to
    ``max_retries`` times before raising HttpRequestError.
    """
    if session is None:
        session = create_session()

    last_exc: Optional[BaseException] = None

    for attempt in range(1, max_retries + 1):
        try:
            LOG.debug("Fetching %s (attempt %d/%d)", url, attempt, max_retries)
            response = session.get(url, timeout=timeout)
        except requests.RequestException as exc:  # network or protocol error
            last_exc = exc
            LOG.warning("Request error for %s: %s", url, exc)
        else:
            if 200 <= response.status_code < 300:
                # Help requests choose a reasonable encoding if the server
                # does not specify one.
                if not response.encoding:
                    response.encoding = response.apparent_encoding  # type: ignore[attr-defined]
                return response.text

            LOG.warning(
                "Unexpected status %s for %s",
                response.status_code,
                url,
            )

        if attempt < max_retries:
            continue

    message = f"Failed to fetch {url!r} after {max_retries} attempts"
    if last_exc:
        raise HttpRequestError(message) from last_exc
    raise HttpRequestError(message)
