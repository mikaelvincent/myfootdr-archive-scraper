"""Command-line interface for the My FootDr archive scraper.

This module crawls archived "Our Clinics" pages via the Wayback Machine and can:

* print a deduplicated list of discovered URLs
* emit extracted clinic records as JSON
* write clinic records to a CSV file, together with basic validation reports
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
from .output import validate_clinics, write_clinics_csv, write_incomplete_clinics_csv

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
            "Optional path to save output to a file. In 'urls' mode this writes "
            "a newline-separated text file of discovered URLs. In 'clinics-json' "
            "mode it writes JSON instead of printing to stdout. In 'clinics-csv' "
            "mode it sets the output CSV path (defaults to 'clinics.csv')."
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
        choices=("urls", "clinics-json", "clinics-csv"),
        default="urls",
        help=(
            "Output mode: 'urls' (default) prints discovered /our-clinics/ URLs; "
            "'clinics-json' prints extracted clinic records as JSON; "
            "'clinics-csv' writes clinic records to a CSV file."
        ),
    )
    parser.add_argument(
        "--incomplete-out",
        type=Path,
        metavar="PATH",
        default=None,
        help=(
            "When using 'clinics-csv' mode, optional path to write a CSV "
            "containing only clinics that are missing critical fields "
            "(name, address, or phone)."
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


def _serialise_clinics_to_json(clinics) -> tuple[list[dict], str]:
    """Convert Clinic instances into a JSON string.

    Returns a (data, text) tuple where *data* is the list of dictionaries and *text* is the formatted JSON
    representation.
    """
    from .clinic_models import Clinic  # Local import to avoid cycles in type checking

    data: list[dict] = []
    for clinic in clinics:
        if not isinstance(clinic, Clinic):
            continue
        data.append(clinic.to_json_dict())

    text = json.dumps(data, indent=2, ensure_ascii=False)
    return data, text


def print_clinics_as_json(clinics) -> None:
    """Print a list of Clinic instances as JSON to stdout."""
    _, text = _serialise_clinics_to_json(clinics)
    print(text)


def save_clinics_as_json(path: Path, clinics) -> None:
    """Save clinic records as formatted JSON."""
    data, text = _serialise_clinics_to_json(clinics)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    LOG.info("Saved %d clinics as JSON to %s", len(data), path)


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
        if args.out is not None:
            save_clinics_as_json(args.out, result.clinics)
        else:
            print_clinics_as_json(result.clinics)
    elif args.mode == "clinics-csv":
        csv_path = args.out or Path("clinics.csv")
        clinic_count = write_clinics_csv(result.clinics, csv_path)
        LOG.info("Wrote %d clinics to %s", clinic_count, csv_path)

        report = validate_clinics(result.clinics)
        LOG.info(
            "Validation: %d clinics extracted (%d complete, %d incomplete).",
            report.total_clinics,
            report.complete_clinics,
            report.incomplete_clinics,
        )
        LOG.info(
            "Missing fields - name: %d, address: %d, email: %d, phone: %d, services: %d.",
            report.missing_name,
            report.missing_address,
            report.missing_email,
            report.missing_phone,
            report.missing_services,
        )

        if args.incomplete_out is not None:
            incomplete_count = write_incomplete_clinics_csv(
                result.clinics,
                args.incomplete_out,
            )
            if incomplete_count:
                LOG.info(
                    "Wrote %d incomplete clinics to %s",
                    incomplete_count,
                    args.incomplete_out,
                )
            else:
                LOG.info(
                    "No incomplete clinics detected; %s was not created.",
                    args.incomplete_out,
                )
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
