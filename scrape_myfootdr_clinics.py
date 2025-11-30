#!/usr/bin/env python3
"""Entry point script for the My FootDr archive scraper.

This delegates to the CLI module, which crawls archived 'Our Clinics' pages and either prints a deduplicated list of
discovered URLs or emits extracted clinic records as JSON.
"""

from myfootdr_scraper.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
