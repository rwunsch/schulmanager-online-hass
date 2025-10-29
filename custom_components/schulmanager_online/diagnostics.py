"""Diagnostics support for Schulmanager Online."""
from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

REDACT_KEYS = {
    "email",
    "username",
    "password",
    "jwt",
    "token",
    "authorization",
    "hash",
    "salt",
    "firstname",
    "lastname",
    "name",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry with secrets redacted."""
    runtime = hass.data.get(entry.domain, {}).get(entry.entry_id, {})
    coord = runtime.get("coordinator")
    api = runtime.get("api")
    students = runtime.get("students", [])

    # Gather multi-school information
    multi_school_info = {
        "has_institution_id_in_config": "institution_id" in entry.data,
        "institution_id_value": entry.data.get("institution_id"),
        "api_has_multiple_accounts": bool(getattr(api, "multiple_accounts", None)),
        "multiple_accounts_count": len(getattr(api, "multiple_accounts", []) or []),
        "api_institution_id": getattr(api, "institution_id", None),
    }
    
    # Check students structure
    student_diagnostics = []
    for student in students:
        student_diagnostics.append({
            "id": student.get("id"),
            "has_institution_id_field": "institutionId" in student,
            "institution_id_if_present": student.get("institutionId"),
            "has__institution_id_field": "_institution_id" in student,
            "_institution_id": student.get("_institution_id"),
            "_institution_name": student.get("_institution_name"),
            "class_id": student.get("classId"),
        })

    data = {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
            "version": entry.version,
        },
        "multi_school": multi_school_info,
        "students": {
            "count": len(students),
            "details": student_diagnostics,
        },
        "service": {
            "has_token": bool(getattr(api, "token", None)),
            "token_expires": str(getattr(api, "token_expires", None)),
            "has_bundle_version": bool(getattr(api, "bundle_version", None)),
            "bundle_version": getattr(api, "bundle_version", None),
        },
        "coordinator": {
            "last_update_success": getattr(coord, "last_update_success", None),
            "last_exception": str(getattr(coord, "last_exception", None)) if getattr(coord, "last_exception", None) else None,
        },
    }
    return async_redact_data(data, REDACT_KEYS)


