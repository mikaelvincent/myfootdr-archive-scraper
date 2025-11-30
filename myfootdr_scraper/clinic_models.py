"""Data models for extracted clinic information."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple


def _normalize_for_dedup(value: Optional[str]) -> str:
    """Normalise a free-text field for use in de-duplication keys."""
    if not value:
        return ""
    # Collapse whitespace and lowercase for stable comparisons.
    return " ".join(value.split()).strip().lower()


@dataclass
class Clinic:
    """Structured representation of a single clinic page."""

    original_url: str
    name: Optional[str] = None
    address: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    services: List[str] = field(default_factory=list)

    def dedup_key(self) -> Tuple[str, str]:
        """Return a key suitable for de-duplicating clinics.

        Uses a normalised (name, address) pair so that the same clinic reached via multiple paths is only recorded once.
        """
        return (_normalize_for_dedup(self.name), _normalize_for_dedup(self.address))

    def non_empty_field_count(self) -> int:
        """Return a simple completeness score used when merging duplicates."""
        count = 0
        if self.name:
            count += 1
        if self.address:
            count += 1
        if self.email:
            count += 1
        if self.phone:
            count += 1
        if self.services:
            count += 1
        return count

    def to_json_dict(self) -> dict[str, Any]:
        """Serialise the clinic to a JSON-friendly dictionary."""
        return {
            "original_url": self.original_url,
            "name": self.name,
            "address": self.address,
            "email": self.email,
            "phone": self.phone,
            "services": list(self.services),
        }
