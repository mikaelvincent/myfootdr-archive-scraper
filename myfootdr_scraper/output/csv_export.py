"""CSV export helpers for clinic data."""

from __future__ import annotations

from csv import DictWriter
from pathlib import Path
from typing import Iterable

from ..clinic_models import Clinic
from .common import CSV_COLUMNS


def clinic_to_row(clinic: Clinic) -> dict[str, str]:
    """Convert a Clinic instance into a flat CSV row."""
    return {
        "Name of Clinic": clinic.name or "",
        "Address": clinic.address or "",
        "Email": clinic.email or "",
        "Phone": clinic.phone or "",
        "Services": "; ".join(clinic.services) if clinic.services else "",
    }


def write_clinics_csv(clinics: Iterable[Clinic], path: Path) -> int:
    """Write *clinics* to *path* as a CSV file.

    Returns the number of clinics written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for clinic in clinics:
            writer.writerow(clinic_to_row(clinic))
            count += 1
    return count
