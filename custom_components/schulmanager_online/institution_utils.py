"""Shared helpers for building institution display info (name/city/address)."""
from __future__ import annotations

from typing import Any, Dict, NamedTuple


class InstitutionDisplayInfo(NamedTuple):
    """Display-ready institution fields derived from a get-institution API response."""

    name: str
    name_short: str
    city: str
    address: str


def build_institution_display_info(
    institution_data: Dict[str, Any], fallback_name: str
) -> InstitutionDisplayInfo:
    """Build a display name, short name, city and address from institution API data.

    The API sometimes includes the city as a suffix of ``name`` (e.g.
    "Gymnasium MusterstadtMusterstadt"); in that case the city is split off
    and re-joined with a separator so it isn't shown twice.
    """
    raw_name = institution_data.get("name", fallback_name)
    city = institution_data.get("city", "")
    street = institution_data.get("street", "")
    zipcode = institution_data.get("zipcode", "")

    if city and city in raw_name:
        name_short = raw_name.replace(city, "").strip()
        name = f"{name_short} | {city}"
    else:
        name = raw_name
        name_short = raw_name

    if street and zipcode and city:
        address = f"{street}, {zipcode} {city}"
    elif street and city:
        address = f"{street}, {city}"
    elif city:
        address = city
    else:
        address = ""

    return InstitutionDisplayInfo(name=name, name_short=name_short, city=city, address=address)
