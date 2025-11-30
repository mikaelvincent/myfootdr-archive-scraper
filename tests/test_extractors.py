"""Unit tests for clinic extraction helpers."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from myfootdr_scraper.clinic_extraction import (
    extract_clinic_from_html,
    extract_clinic_name,
    extract_services,
    is_clinic_page,
)
from myfootdr_scraper.html_utils import parse_html


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "clinic_pages"


class ClinicExtractionTestCase(unittest.TestCase):
    def test_extract_full_clinic_from_noosa_fixture(self) -> None:
        html = (FIXTURES_DIR / "noosa_basic.html").read_text(encoding="utf-8")
        clinic = extract_clinic_from_html(
            html, "https://www.myfootdr.com.au/our-clinics/sunshine-coast/noosa/"
        )
        self.assertIsNotNone(clinic)
        assert clinic is not None  # type narrowing for mypy-like tools

        self.assertEqual("Allsports Podiatry Noosa", clinic.name)
        self.assertEqual(
            "Unit 4, 17 Sunshine Beach Rd Noosa QLD 4567",
            clinic.address,
        )
        self.assertEqual("noosa@example.com", clinic.email)
        self.assertEqual("(07) 1234 5678", clinic.phone)
        self.assertEqual(
            ["General podiatry", "Ingrown toenail treatment", "Custom orthotics"],
            clinic.services,
        )

    def test_extract_name_from_breadcrumb_fallback(self) -> None:
        html = (FIXTURES_DIR / "clinic_with_breadcrumb.html").read_text(
            encoding="utf-8"
        )
        soup = parse_html(html)
        name = extract_clinic_name(soup)
        self.assertEqual("Allsports Podiatry Noosa", name)

    def test_extract_services_marker_phrase(self) -> None:
        html = (FIXTURES_DIR / "clinic_with_breadcrumb.html").read_text(
            encoding="utf-8"
        )
        soup = parse_html(html)
        services = extract_services(soup)
        self.assertEqual(["Sports podiatry", "Children's foot care"], services)

    def test_region_page_is_not_clinic(self) -> None:
        html = (FIXTURES_DIR / "region_not_clinic.html").read_text(encoding="utf-8")
        soup = parse_html(html)
        self.assertFalse(is_clinic_page(soup))

    def test_clinic_serialises_to_json(self) -> None:
        html = (FIXTURES_DIR / "noosa_basic.html").read_text(encoding="utf-8")
        clinic = extract_clinic_from_html(
            html, "https://www.myfootdr.com.au/our-clinics/sunshine-coast/noosa/"
        )
        assert clinic is not None
        data = clinic.to_json_dict()
        # Ensure the result is JSON serialisable and contains core keys.
        encoded = json.dumps(data)
        self.assertIn("Allsports Podiatry Noosa", encoded)
        self.assertIn("noosa@example.com", encoded)


if __name__ == "__main__":
    unittest.main()
