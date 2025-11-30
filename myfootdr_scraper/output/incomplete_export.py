"""Helpers for exporting only incomplete clinic records."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

from ..clinic_models import Clinic
from .csv_export import write_clinics_csv


def _is_incomplete(clinic: Clinic) -> bool:
    """Return True if *clinic* is missing any critical fields.

    Critical fields are name, address, and phone.
    """
    return not clinic.name or not clinic.address or not clinic.phone


def write_incomplete_clinics_csv(clinics: Iterable[Clinic], path: Path) -> int:
    """Write a CSV containing only incomplete clinics.

    Returns the number of clinics written. If no clinics are incomplete, the file is not created and zero is returned.
    """
    incomplete: List[Clinic] = [clinic for clinic in clinics if _is_incomplete(clinic)]
    if not incomplete:
        return 0
    return write_clinics_csv(incomplete, path)
