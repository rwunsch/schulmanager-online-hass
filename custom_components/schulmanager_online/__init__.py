"""The Schulmanager Online integration."""
from __future__ import annotations

import logging
from typing import Any, Dict

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
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
    
    # Register custom card resources
    await _register_custom_cards(hass)
    
    session = async_get_clientsession(hass)
    api = SchulmanagerAPI(email, password, session)
    
    try:
        # Test authentication
        await api.authenticate()
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
    
    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    await hass.config_entries.async_reload(entry.entry_id)


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
