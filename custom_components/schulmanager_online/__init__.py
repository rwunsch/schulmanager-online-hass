"""The Schulmanager Online integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import (
    async_get as async_get_device_registry,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SchulmanagerAPI
from .const import CONF_EMAIL, CONF_PASSWORD, DOMAIN
from .coordinator import SchulmanagerDataUpdateCoordinator
from .institution_utils import build_institution_display_info
from .devices import async_register_devices

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.CALENDAR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schulmanager Online from a config entry."""
    email = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]
    schools = entry.data.get("schools", [])
    
    # Register custom card resources
    await _register_custom_cards(hass)
    
    session = async_get_clientsession(hass)
    
    # Create API instances and collect students
    api_instances = {}
    all_students = []
    
    try:
        if schools:
            # Multi-school account: Create API instance per school
            _LOGGER.info("Setting up multi-school account with %d schools", len(schools))
            
            for school in schools:
                school_id = school.get("id")
                school_name = school.get("name")
                
                if not school_id:
                    _LOGGER.warning("Skipping school with no ID: %s", school)
                    continue
                
                try:
                    _LOGGER.info("Setting up API for school: %s (ID: %d)", school_name, school_id)
                    
                    # Create API instance for this school
                    school_api = SchulmanagerAPI(email, password, session)
                    await school_api.authenticate(institution_id=school_id)
                    
                    # Get students from this school
                    school_students = await school_api.get_students()

                    # Institution display info was resolved once during the config
                    # flow and cached in entry.data; reuse it instead of hitting
                    # get-institution again on every Home Assistant start. Older
                    # entries created before this caching existed fall back to
                    # fetching it live.
                    institution_name_short = school.get("name_short", school_name)
                    institution_city = school.get("city", "")
                    institution_address = school.get("address", "")

                    if not school.get("name_short"):
                        try:
                            institution_data = await school_api.get_institution()
                            info = build_institution_display_info(institution_data, school_name)
                            school_name = info.name
                            institution_name_short = info.name_short
                            institution_city = info.city
                            institution_address = info.address
                        except Exception as e:
                            _LOGGER.warning("Could not fetch detailed info for school %d: %s", school_id, e)
                    
                    # Add institution info to each student
                    for student in school_students:
                        student["_institution_id"] = school_id
                        student["_institution_name"] = school_name
                        student["_institution_name_short"] = institution_name_short
                        student["_institution_city"] = institution_city
                        student["_institution_address"] = institution_address
                        all_students.append(student)
                    
                    # Store API instance
                    api_instances[school_id] = school_api
                    
                    _LOGGER.info("Found %d students in %s", len(school_students), school_name)
                    
                except Exception as e:
                    _LOGGER.error("Failed to setup school %s (ID: %d): %s", school_name, school_id, e)
                    # Continue with other schools even if one fails
                    continue
            
            if not all_students:
                _LOGGER.error("No students found across any schools for account %s", email)
                return False
                
            _LOGGER.info("Total students found across all schools: %d", len(all_students))
            
        else:
            # Single school account (legacy support)
            _LOGGER.info("Setting up single-school account")
            institution_id = entry.data.get("institution_id")
            
            api = SchulmanagerAPI(email, password, session)
            await api.authenticate(institution_id=institution_id)
            students = await api.get_students()
            
            if not students:
                _LOGGER.error("No students found for account %s", email)
                return False
            
            # Add institution info if available
            if api.institution_id:
                # Try to fetch institution details from API endpoint
                institution_name = f"School {api.institution_id}"  # Fallback
                institution_name_short = institution_name
                institution_city = ""
                institution_address = ""
                
                try:
                    # First check if we have it in entry data (from config flow)
                    if entry.data.get("institution_name"):
                        institution_name = entry.data["institution_name"]
                        institution_name_short = entry.data.get("institution_name_short", institution_name)
                        institution_city = entry.data.get("institution_city", "")
                        institution_address = entry.data.get("institution_address", "")
                        _LOGGER.debug("Using institution data from config: %s", institution_name)
                    else:
                        # Fetch from API using the new get-institution endpoint
                        institution_data = await api.get_institution()
                        info = build_institution_display_info(institution_data, institution_name)
                        institution_name = info.name
                        institution_name_short = info.name_short
                        institution_city = info.city
                        institution_address = info.address

                        _LOGGER.info("✅ Retrieved institution from API: %s", institution_name)
                except Exception as e:
                    _LOGGER.warning("Could not fetch institution details: %s (using fallback)", e)
                
                for student in students:
                    student["_institution_id"] = api.institution_id
                    student["_institution_name"] = institution_name
                    student["_institution_name_short"] = institution_name_short
                    student["_institution_city"] = institution_city
                    student["_institution_address"] = institution_address
                
                _LOGGER.info("Added institution info: ID=%d, Name=%s", api.institution_id, institution_name)
                api_instances[api.institution_id] = api
            else:
                # No institution ID - use generic key
                _LOGGER.warning("No institution_id available for account")
                api_instances[0] = api
            
            all_students = students
            _LOGGER.info("Found %d students for account %s", len(students), email)
        
    except Exception as e:
        _LOGGER.error("Failed to authenticate or get students: %s", e)
        return False
    
    # Create coordinator with API instances
    coordinator = SchulmanagerDataUpdateCoordinator(hass, api_instances, entry.options)
    
    # Store coordinator, API instances, and students in hass data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "api_instances": api_instances,
        "students": all_students,
        "schools": schools,
    }
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    # Register before platforms so their existing identifiers resolve in this entry.
    async_register_devices(async_get_device_registry(hass), entry.entry_id, all_students)

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Set up options update listener
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Register services once per run
    await _async_register_services(hass)
    
    return True


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

    if config_entry.version < 2:
        # Migration from version 1 to 2 (no data changes required)
        hass.config_entries.async_update_entry(config_entry, version=2)

    if config_entry.version < 3:
        # Version 3: sensor/calendar unique_ids switched from being keyed by
        # the student's (possibly colliding, possibly changing) display name
        # to the stable student_id. Rewrite existing registry entries in
        # place so entity history/customizations survive the upgrade.
        await _async_migrate_unique_ids_to_student_id(hass, config_entry)
        hass.config_entries.async_update_entry(config_entry, version=3)

    _LOGGER.info("Migration to version %s successful", config_entry.version)
    return True


async def _async_migrate_unique_ids_to_student_id(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> None:
    """Rewrite name-based sensor/calendar unique_ids to student-id-based ones."""
    try:
        session = async_get_clientsession(hass)
        email = config_entry.data.get(CONF_EMAIL)
        password = config_entry.data.get(CONF_PASSWORD)
        schools = config_entry.data.get("schools", [])

        if not email or not password:
            _LOGGER.warning("Skipping unique_id migration: missing credentials")
            return

        students: list = []
        school_ids = [s.get("id") for s in schools if s.get("id")] or [
            config_entry.data.get("institution_id")
        ]

        for school_id in school_ids:
            try:
                api = SchulmanagerAPI(email, password, session)
                await api.authenticate(institution_id=school_id)
                students.extend(await api.get_students())
            except Exception as e:
                _LOGGER.warning(
                    "Skipping unique_id migration for school %s: %s", school_id, e
                )

        if not students:
            _LOGGER.warning("Unique_id migration skipped: no students resolved")
            return

        entity_registry = er.async_get(hass)
        entries = er.async_entries_for_config_entry(entity_registry, config_entry.entry_id)

        for student in students:
            student_id = student.get("id")
            if not student_id:
                continue

            name = f"{student.get('firstname', '')} {student.get('lastname', '')}"
            safe_name = name.lower().replace(" ", "_").replace("-", "_")
            safe_name = "".join(c for c in safe_name if c.isalnum() or c == "_")
            if not safe_name:
                continue

            old_suffix = f"_{safe_name}"
            for entity in entries:
                if not entity.unique_id.endswith(old_suffix):
                    continue
                new_unique_id = f"{entity.unique_id[: -len(old_suffix)]}_{student_id}"
                if new_unique_id == entity.unique_id:
                    continue
                _LOGGER.info(
                    "Migrating %s unique_id '%s' -> '%s'",
                    entity.entity_id, entity.unique_id, new_unique_id,
                )
                try:
                    entity_registry.async_update_entity(
                        entity.entity_id, new_unique_id=new_unique_id
                    )
                except Exception as e:
                    _LOGGER.warning(
                        "Could not migrate unique_id for %s: %s", entity.entity_id, e
                    )
    except Exception:
        _LOGGER.exception("Unique_id migration to student_id-based scheme failed")


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
            api_instances = data.get("api_instances", {})

            for school_api in api_instances.values():
                try:
                    school_api.token = None
                    school_api.token_expires = None
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
