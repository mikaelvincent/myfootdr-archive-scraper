#!/usr/bin/env python3
"""Entry point script for the My FootDr archive scraper.

This delegates to the CLI module, which crawls archived 'Our Clinics' pages and prints a deduplicated list of discovered
URLs.
"""

from myfootdr_scraper.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
