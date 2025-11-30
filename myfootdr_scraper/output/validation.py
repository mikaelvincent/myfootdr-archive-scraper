"""Simple validation for extracted clinic datasets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from ..clinic_models import Clinic


@dataclass
class ValidationReport:
    """Summary statistics for a batch of clinics."""

    total_clinics: int
    incomplete_clinics: int
    missing_name: int
    missing_address: int
    missing_email: int
    missing_phone: int
    missing_services: int

    @property
    def complete_clinics(self) -> int:
        """Return the number of clinics with all critical fields present."""
        return self.total_clinics - self.incomplete_clinics


def validate_clinics(clinics: Iterable[Clinic]) -> ValidationReport:
    """Generate a ValidationReport for the given clinics.

    A clinic is considered "incomplete" if any of the critical fields (name, address, or phone) are missing.
    """
    total = 0
    incomplete = 0
    missing_name = 0
    missing_address = 0
    missing_email = 0
    missing_phone = 0
    missing_services = 0

    for clinic in clinics:
        total += 1

        has_name = bool(clinic.name)
        has_address = bool(clinic.address)
        has_email = bool(clinic.email)
        has_phone = bool(clinic.phone)
        has_services = bool(clinic.services)

        if not has_name:
            missing_name += 1
        if not has_address:
            missing_address += 1
        if not has_email:
            missing_email += 1
        if not has_phone:
            missing_phone += 1
        if not has_services:
            missing_services += 1

        if not (has_name and has_address and has_phone):
            incomplete += 1

    return ValidationReport(
        total_clinics=total,
        incomplete_clinics=incomplete,
        missing_name=missing_name,
        missing_address=missing_address,
        missing_email=missing_email,
        missing_phone=missing_phone,
        missing_services=missing_services,
    )
