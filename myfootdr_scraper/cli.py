"""Command-line interface for the My FootDr archive scraper.

For Sprint 1 this only fetches a single page and prints its <title>.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional

from .config import DEFAULT_BASE_URL
from .http_client import HttpRequestError, create_session, fetch_html
from .html_utils import extract_title

LOG = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Fetch a single My FootDr clinics archive page and " "print its <title>."
        )
    )
    parser.add_argument(
        "--base-url",
        dest="base_url",
        default=DEFAULT_BASE_URL,
        help=(
            "Wayback URL to start from. Defaults to the July 2025 "
            "snapshot of the 'Our Clinics' page."
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        metavar="PATH",
        default=None,
        help=(
            "Optional path to save the raw HTML response. "
            "Useful when inspecting page structure in early sprints."
        ),
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging.",
    )
    return parser


def configure_logging(debug: bool) -> None:
    """Configure global logging for the CLI run."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


def save_html(html: str, path: Path) -> None:
    """Write the fetched HTML to a file for later inspection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    LOG.info("Saved HTML to %s", path)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Returns an exit code compatible with sys.exit().
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.debug)

    session = create_session()
    try:
        html = fetch_html(args.base_url, session=session)
    except HttpRequestError as exc:
        LOG.error("Failed to fetch base URL: %s", exc)
        return 1

    title = extract_title(html) or "(no title found)"
    print(title)

    if args.out is not None:
        save_html(html, args.out)

    return 0
