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
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry with secrets redacted."""
    runtime = hass.data.get(entry.domain, {}).get(entry.entry_id, {})
    coord = runtime.get("coordinator")
    api = runtime.get("api")

    data = {
        "entry": {
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
            "version": entry.version,
        },
        "service": {
            "has_token": bool(getattr(api, "token", None)),
            "has_bundle_version": bool(getattr(api, "bundle_version", None)),
        },
        "coordinator": {
            "last_update_success": getattr(coord, "last_update_success", None),
        },
    }
    return async_redact_data(data, REDACT_KEYS)


