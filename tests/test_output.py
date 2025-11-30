"""Unit tests for CSV export and validation helpers."""

from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from myfootdr_scraper.clinic_models import Clinic
from myfootdr_scraper.output import (
    validate_clinics,
    write_clinics_csv,
    write_incomplete_clinics_csv,
)


class OutputHelpersTestCase(unittest.TestCase):
    def test_write_clinics_csv_writes_expected_columns_and_rows(self) -> None:
        clinics = [
            Clinic(
                original_url="https://example.com/clinic-a",
                name="Clinic A",
                address="123 Example Street",
                email="a@example.com",
                phone="0123 456 789",
                services=["Service 1", "Service 2"],
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "clinics.csv"
            count = write_clinics_csv(clinics, path)
            self.assertEqual(1, count)
            self.assertTrue(path.exists())

            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                self.assertEqual(
                    [
                        "Name of Clinic",
                        "Address",
                        "Email",
                        "Phone",
                        "Services",
                    ],
                    reader.fieldnames,
                )
                rows = list(reader)
                self.assertEqual(1, len(rows))
                row = rows[0]
                self.assertEqual("Clinic A", row["Name of Clinic"])
                self.assertEqual("123 Example Street", row["Address"])
                self.assertEqual("a@example.com", row["Email"])
                self.assertEqual("0123 456 789", row["Phone"])
                self.assertEqual("Service 1; Service 2", row["Services"])

    def test_validate_clinics_counts_missing_fields(self) -> None:
        complete = Clinic(
            original_url="https://example.com/complete",
            name="Complete Clinic",
            address="1 Main St",
            email="complete@example.com",
            phone="0000 000 000",
            services=["Service"],
        )
        missing_phone = Clinic(
            original_url="https://example.com/missing-phone",
            name="No Phone Clinic",
            address="2 Side St",
            email="nophone@example.com",
            phone=None,
            services=[],
        )

        report = validate_clinics([complete, missing_phone])

        self.assertEqual(2, report.total_clinics)
        self.assertEqual(1, report.incomplete_clinics)
        self.assertEqual(0, report.missing_name)
        self.assertEqual(0, report.missing_address)
        self.assertEqual(0, report.missing_email)
        self.assertEqual(1, report.missing_phone)
        self.assertEqual(1, report.missing_services)
        self.assertEqual(1, report.complete_clinics)

    def test_write_incomplete_clinics_csv_filters_incomplete_only(self) -> None:
        complete = Clinic(
            original_url="https://example.com/complete",
            name="Complete Clinic",
            address="1 Main St",
            email="complete@example.com",
            phone="0000 000 000",
            services=["Service"],
        )
        missing_name = Clinic(
            original_url="https://example.com/missing-name",
            name=None,
            address="2 Side St",
            email="noname@example.com",
            phone="1111 111 111",
            services=[],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "clinics_incomplete.csv"
            count = write_incomplete_clinics_csv([complete, missing_name], path)
            self.assertEqual(1, count)
            self.assertTrue(path.exists())

            with path.open(newline="", encoding="utf-8") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
                self.assertEqual(1, len(rows))
                row = rows[0]
                self.assertEqual(
                    "",
                    row["Name of Clinic"],
                )
                self.assertEqual("2 Side St", row["Address"])

    def test_write_incomplete_clinics_csv_does_nothing_when_all_complete(self) -> None:
        clinic = Clinic(
            original_url="https://example.com/complete",
            name="Complete Clinic",
            address="1 Main St",
            email="complete@example.com",
            phone="0000 000 000",
            services=["Service"],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "clinics_incomplete.csv"
            count = write_incomplete_clinics_csv([clinic], path)
            self.assertEqual(0, count)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
