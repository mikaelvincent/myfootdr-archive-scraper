"""HTML-related helper functions for parsing and inspection."""

from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup


def parse_html(html: str) -> BeautifulSoup:
    """Parse raw HTML into a BeautifulSoup tree.

    Uses the lxml parser for robustness when dealing with archived pages.
    """
    return BeautifulSoup(html, "lxml")


def extract_title(html: str) -> Optional[str]:
    """Return the document's title, with a simple heading fallback.

    1. Prefer the <title> element in the <head>.
    2. Fall back to the first <h1> in the document.
    3. Return None if no reasonable title can be found.
    """
    soup = parse_html(html)

    if soup.title and soup.title.string:
        title_text = soup.title.string.strip()
        if title_text:
            return title_text

    heading = soup.find("h1")
    if heading:
        heading_text = heading.get_text(strip=True)
        if heading_text:
            return heading_text

    return None
