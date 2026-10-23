"""Entry-scoped device registration (Home Assistant 2026.10 and newer)."""
from __future__ import annotations

import logging

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceRegistry

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def async_register_devices(registry: DeviceRegistry, entry_id: str, students: list) -> None:
    """Preserve registry IDs, aliases and user metadata without deleting devices.

    If legacy and current aliases identify different devices, do not combine
    them: HA's collision reconciliation can delete the other device, including
    user metadata and links which an entity-only check cannot establish as safe.
    """
    service = registry.async_get_or_create(
        config_entry_id=entry_id,
        identifiers={(DOMAIN, f"service_{entry_id}")},
        name="Schulmanager Online",
        manufacturer="Schulmanager Online",
        model="Portal",
        entry_type=DeviceEntryType.SERVICE,
    )
    for student in students:
        sid = student.get("id")
        if sid is None:
            _LOGGER.warning("Skipping device registration for student without ID")
            continue
        current = (DOMAIN, str(sid))
        legacy = (DOMAIN, f"student_{sid}")
        current_device = registry.async_get_device_by_identifier(current, entry_id)
        legacy_device = registry.async_get_device_by_identifier(legacy, entry_id)
        existing = current_device or legacy_device
        identifiers = set(existing.identifiers) if existing else set()
        if current_device and legacy_device and current_device.id != legacy_device.id:
            _LOGGER.warning(
                "Separate current and legacy student devices in entry %s; "
                "preserving both devices and their assignments without merging",
                entry_id,
            )
            identifiers.add(current)
        else:
            identifiers.update((current, legacy))
        registry.async_get_or_create(
            config_entry_id=entry_id,
            identifiers=identifiers,
            name=f"{student.get('firstname', '')} {student.get('lastname', '')}".strip() or "Student",
            manufacturer="Schulmanager Online",
            model="Student Schedule",
            via_device_id=service.id,
        )
