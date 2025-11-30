#!/usr/bin/env python3
"""Entry point script for the My FootDr archive scraper.

For Sprint 1 this delegates to the CLI module, which fetches a single page and prints its <title>.
"""

from myfootdr_scraper.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
