"""Unit tests for URL helpers."""

from __future__ import annotations

import unittest

from myfootdr_scraper.urls import (
    canonicalize_original_url,
    canonicalize_wayback_url,
    extract_original_url,
    extract_wayback_timestamp,
    is_in_scope_wayback_url,
    is_our_clinics_original_url,
    is_probable_clinic_url,
)


class UrlHelpersTestCase(unittest.TestCase):
    def test_extract_original_from_wayback(self) -> None:
        wayback = (
            "https://web.archive.org/web/20250708180027/"
            "https://www.myfootdr.com.au/our-clinics/"
        )
        original = extract_original_url(wayback)
        self.assertEqual(
            "https://www.myfootdr.com.au/our-clinics/",
            original,
        )

    def test_extract_original_returns_none_for_non_wayback(self) -> None:
        original = extract_original_url(
            "https://www.myfootdr.com.au/our-clinics/noosa/"
        )
        self.assertIsNone(original)

    def test_extract_wayback_timestamp_parses_plain_timestamp(self) -> None:
        wayback = (
            "https://web.archive.org/web/20250708180027/"
            "https://www.myfootdr.com.au/our-clinics/"
        )
        timestamp = extract_wayback_timestamp(wayback)
        self.assertEqual(20250708180027, timestamp)

    def test_extract_wayback_timestamp_ignores_suffixes(self) -> None:
        wayback = (
            "https://web.archive.org/web/20250708180027im_/"
            "https://www.myfootdr.com.au/our-clinics/"
        )
        timestamp = extract_wayback_timestamp(wayback)
        self.assertEqual(20250708180027, timestamp)

    def test_is_our_clinics_original_true(self) -> None:
        url = "https://www.myfootdr.com.au/our-clinics/sunshine-coast/noosa/"
        self.assertTrue(is_our_clinics_original_url(url))

    def test_is_our_clinics_original_false_for_other_path(self) -> None:
        url = "https://www.myfootdr.com.au/blog/some-article/"
        self.assertFalse(is_our_clinics_original_url(url))

    def test_in_scope_wayback_url_true(self) -> None:
        wayback = (
            "https://web.archive.org/web/20250708180027/"
            "https://www.myfootdr.com.au/our-clinics/noosa/"
        )
        self.assertTrue(is_in_scope_wayback_url(wayback))

    def test_in_scope_wayback_url_false_for_non_wayback(self) -> None:
        url = "https://www.myfootdr.com.au/our-clinics/noosa/"
        self.assertFalse(is_in_scope_wayback_url(url))

    def test_canonicalize_original_url_normalises_scheme_and_strips_extras(
        self,
    ) -> None:
        original = (
            "http://www.myfootdr.com.au/our-clinics/noosa/" "?utm_source=test#section"
        )
        canonical = canonicalize_original_url(original)
        self.assertEqual(
            "https://www.myfootdr.com.au/our-clinics/noosa",
            canonical,
        )

    def test_canonicalize_wayback_url_normalises_case_and_trailing(self) -> None:
        url = (
            "HTTP://WEB.ARCHIVE.ORG/web/20250708180027/"
            "https://www.myfootdr.com.au/our-clinics/noosa/"
        )
        canonical = canonicalize_wayback_url(url)
        self.assertEqual(
            "http://web.archive.org/web/20250708180027/"
            "https://www.myfootdr.com.au/our-clinics/noosa",
            canonical,
        )

    def test_is_probable_clinic_url_true_for_deep_path(self) -> None:
        url = "https://www.myfootdr.com.au/our-clinics/sunshine-coast/noosa/"
        self.assertTrue(is_probable_clinic_url(url))

    def test_is_probable_clinic_url_false_for_region_index(self) -> None:
        url = "https://www.myfootdr.com.au/our-clinics/brisbane/"
        self.assertFalse(is_probable_clinic_url(url))


if __name__ == "__main__":
    unittest.main()
