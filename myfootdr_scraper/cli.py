"""Command-line interface for the My FootDr archive scraper.

For Sprint 2 this crawls archived "Our Clinics" pages via the Wayback Machine and prints a deduplicated list of
discovered URLs.

From Sprint 3 onward it can also extract clinic records and emit them as JSON.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
from typing import Optional

from .config import DEFAULT_BASE_URL
from .crawler import crawl_our_clinics
from .http_client import create_session

LOG = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Create the top-level argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Discover archived My FootDr 'Our Clinics' URLs from the Wayback Machine "
            "and optionally extract clinic details."
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
            "Optional path to save the discovered URLs as a newline-"
            "separated text file. Only used in 'urls' mode."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        metavar="N",
        default=None,
        help=(
            "Optional maximum number of pages to visit during the crawl "
            "(useful for debugging)."
        ),
    )
    parser.add_argument(
        "--mode",
        choices=("urls", "clinics-json"),
        default="urls",
        help=(
            "Output mode: 'urls' (default) prints discovered /our-clinics/ URLs; "
            "'clinics-json' prints extracted clinic records as JSON."
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


def save_urls(path: Path, urls: list[str]) -> None:
    """Write the discovered URLs to a file, one per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    contents = "\n".join(urls)
    if contents:
        contents += "\n"
    path.write_text(contents, encoding="utf-8")
    LOG.info("Saved %d URLs to %s", len(urls), path)


def print_clinics_as_json(clinics) -> None:
    """Print a list of Clinic instances as JSON to stdout."""
    from .clinic_models import Clinic  # Local import to avoid cycles in type checking

    data = []
    for clinic in clinics:
        if not isinstance(clinic, Clinic):
            continue
        data.append(clinic.to_json_dict())

    text = json.dumps(data, indent=2, ensure_ascii=False)
    print(text)


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point.

    Returns an exit code compatible with sys.exit().
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    configure_logging(args.debug)

    session = create_session()
    result = crawl_our_clinics(
        args.base_url,
        session=session,
        limit=args.limit,
    )

    if args.mode == "clinics-json":
        print_clinics_as_json(result.clinics)
    else:
        urls = sorted(result.discovered_original_urls)
        for url in urls:
            print(url)

        if args.out is not None:
            save_urls(args.out, urls)

        LOG.info(
            "Finished crawl: %d pages visited, %d unique in-scope URLs (%d clinic candidates).",
            result.visited_pages,
            len(result.discovered_original_urls),
            len(result.clinic_candidate_original_urls),
        )

    return 0
