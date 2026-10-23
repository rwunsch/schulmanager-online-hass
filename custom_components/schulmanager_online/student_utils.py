"""Shared helper for resolving the API instance responsible for a student."""
from __future__ import annotations

from typing import Any, Dict

from .api import SchulmanagerAPI


def get_api_for_student(
    student: Dict[str, Any], api_instances: Dict[int, SchulmanagerAPI]
) -> SchulmanagerAPI:
    """Get the correct API instance for a student based on their institution."""
    institution_id = student.get("_institution_id")

    if institution_id and institution_id in api_instances:
        return api_instances[institution_id]

    # Fallback: return first available API instance
    if api_instances:
        return next(iter(api_instances.values()))

    raise ValueError(f"No API instance found for student {student.get('id')}")
