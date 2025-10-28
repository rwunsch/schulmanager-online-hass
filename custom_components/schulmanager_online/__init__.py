"""The Schulmanager Online integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    DeviceEntryType,
    async_get as async_get_device_registry,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SchulmanagerAPI
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import SchulmanagerDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schulmanager Online from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    institution_id = entry.data.get("institution_id")  # For multi-school accounts
    
    # Register custom card resources
    await _register_custom_cards(hass)
    
    session = async_get_clientsession(hass)
    api = SchulmanagerAPI(email, password, session)
    
    try:
        # Test authentication (with institutionId if stored)
        await api.authenticate(institution_id=institution_id)
        students = await api.get_students()
        
        if not students:
            _LOGGER.error("No students found for account %s", email)
            return False
        
        _LOGGER.info("Found %d students for account %s", len(students), email)
        
    except Exception as e:
        _LOGGER.error("Failed to authenticate or get students: %s", e)
        return False
    
    # Create coordinator
    coordinator = SchulmanagerDataUpdateCoordinator(hass, api, entry.options)
    
    # Store coordinator and students in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api": api,
        "students": students,
    }
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Create devices: one service device and child devices per student
    try:
        device_registry = async_get_device_registry(hass)
        entity_registry = er.async_get(hass)
        service_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, f"service_{entry.entry_id}")},
            name="Schulmanager Online",
            manufacturer="Schulmanager Online",
            model="Portal",
            entry_type=DeviceEntryType.SERVICE,
        )
        for student in students:
            sid = student.get("id")
            sname = f"{student.get('firstname', '')} {student.get('lastname', '')}".strip() or "Student"

            # Use both new and legacy identifiers so entities/devices merge
            ident_new = (DOMAIN, str(sid))  # used by sensors/calendars
            ident_old = (DOMAIN, f"student_{sid}")  # legacy identifier (pre-merge)

            # Create or get the unified student device with both identifiers
            student_device = device_registry.async_get_or_create(
                config_entry_id=entry.entry_id,
                identifiers={ident_new, ident_old},
                name=sname,
                manufacturer="Schulmanager Online",
                model="Student Schedule",
                via_device=(DOMAIN, f"service_{entry.entry_id}"),
            )

            # Best-effort cleanup: if a separate legacy-only device exists without entities, remove it
            try:
                legacy_device = device_registry.async_get_device({ident_old})
                unified_device = device_registry.async_get_device({ident_new, ident_old})
                if legacy_device and unified_device and legacy_device.id != unified_device.id:
                    entries = entity_registry.async_entries_for_device(
                        legacy_device.id, include_disabled_entities=True
                    )
                    if not entries:
                        device_registry.async_remove_device(legacy_device.id)
            except Exception:  # defensive; cleanup is best-effort only
                _LOGGER.debug("Legacy device cleanup skipped", exc_info=True)
    except Exception:
        _LOGGER.debug("Device registry setup failed", exc_info=True)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Register services once per run
    await _async_register_services(hass)
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
        # Unregister services if no entries left
        if not hass.data.get(DOMAIN):
            hass.services.async_remove(DOMAIN, "clear_cache")
            hass.services.async_remove(DOMAIN, "refresh")
            hass.services.async_remove(DOMAIN, "clear_debug")
    return unload_ok


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        # Migration from version 1 to 2
        # Add any necessary data migrations here
        config_entry.version = 2

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


async def _register_custom_cards(hass: HomeAssistant) -> None:
    """Register custom Lovelace cards."""
    try:
        from pathlib import Path
        
        # Get the www directory path
        www_path = Path(__file__).parent / "www"
        card_file = www_path / "schulmanager-schedule-card.js"
        
        if not card_file.exists():
            _LOGGER.warning("Card file not found: %s", card_file)
            return
        
        # Use the correct Home Assistant method
        # Copy the card to the www directory for access
        ha_www_dir = Path(hass.config.config_dir) / "www"
        
        # Create www directory if it doesn't exist
        def ensure_www_dir():
            ha_www_dir.mkdir(parents=True, exist_ok=True)
        
        await hass.async_add_executor_job(ensure_www_dir)
        
        target_file = ha_www_dir / "schulmanager-schedule-card.js"
        
        # Copy file content asynchronously
        def copy_card():
            with open(card_file, 'r', encoding='utf-8') as src:
                content = src.read()
            with open(target_file, 'w', encoding='utf-8') as dst:
                dst.write(content)
            _LOGGER.debug("Card file size: %d bytes", len(content))
            return len(content)
        
        file_size = await hass.async_add_executor_job(copy_card)
        _LOGGER.info("✅ Copied card to: %s (%d bytes)", target_file, file_size)
        
        # Verify file exists
        def verify_card():
            exists = target_file.exists()
            size = target_file.stat().st_size if exists else 0
            return exists, size
        
        exists, size = await hass.async_add_executor_job(verify_card)
        _LOGGER.info("Card verification - Exists: %s, Size: %d bytes", exists, size)
        
        if not exists or size == 0:
            _LOGGER.error("❌ Card file copy failed or empty!")
            return
        
        # Register with frontend
        from homeassistant.components.frontend import add_extra_js_url
        card_url = "/local/schulmanager-schedule-card.js"
        add_extra_js_url(hass, card_url)
        _LOGGER.info("✅ Added JS URL to frontend: %s", card_url)
        
        # Check if card content is valid JavaScript
        def check_js_content():
            with open(target_file, 'r', encoding='utf-8') as f:
                content = f.read()
            has_custom_element = 'customElements.define' in content
            has_class_def = 'class SchulmanagerScheduleCard' in content
            return has_custom_element, has_class_def, len(content)
        
        has_element, has_class, content_len = await hass.async_add_executor_job(check_js_content)
        _LOGGER.info("JS Content check - CustomElement: %s, Class: %s, Length: %d", 
                    has_element, has_class, content_len)
        
        _LOGGER.info("🎨 Custom card registration completed successfully")
        
    except Exception as e:
        _LOGGER.error("Failed to register custom cards: %s", e)
        import traceback
        _LOGGER.error("Traceback: %s", traceback.format_exc())


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register Schulmanager Online services (idempotent)."""
    if hass.services.has_service(DOMAIN, "clear_cache"):
        return

    async def _svc_clear_cache(call):
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            entry = data
            api = entry.get("api")
            if api:
                try:
                    api.token = None
                    api.token_expires = None
                except Exception:
                    pass

    async def _svc_refresh(call):
        # Simple cooldown via per-entry attribute on coordinator
        from datetime import datetime, timedelta
        now = datetime.now()
        for entry_id, data in hass.data.get(DOMAIN, {}).items():
            coord = data.get("coordinator")
            if not coord:
                continue
            last = getattr(coord, "_last_manual_refresh", None)
            if last and (now - last).total_seconds() < 300:
                continue  # 5 minutes cooldown
            try:
                await coord.async_request_refresh()
                setattr(coord, "_last_manual_refresh", now)
            except Exception:
                _LOGGER.debug("Manual refresh failed", exc_info=True)

    async def _svc_clear_debug(call):
        from pathlib import Path
        try:
            debug_dir = hass.config.path("custom_components", "schulmanager_online", "debug")
            p = Path(debug_dir)
            if p.exists():
                for child in p.glob("*"):
                    try:
                        if child.is_file():
                            child.unlink()
                    except Exception:
                        pass
        except Exception:
            _LOGGER.debug("Clear debug failed", exc_info=True)

    hass.services.async_register(DOMAIN, "clear_cache", _svc_clear_cache)
    hass.services.async_register(DOMAIN, "refresh", _svc_refresh)
    hass.services.async_register(DOMAIN, "clear_debug", _svc_clear_debug)
