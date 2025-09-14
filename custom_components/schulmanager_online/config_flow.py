"""Config flow for Schulmanager Online integration."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import SchulmanagerAPI, SchulmanagerAPIError
from .const import (
    CONF_LOOKAHEAD_WEEKS, 
    DEFAULT_LOOKAHEAD_WEEKS, 
    CONF_LESSON_DURATION,
    CONF_SHORT_BREAK,
    CONF_LONG_BREAK_1,
    CONF_LONG_BREAK_2,
    CONF_LUNCH_BREAK,
    CONF_SCHOOL_START_TIME,
    DEFAULT_LESSON_DURATION,
    DEFAULT_SHORT_BREAK,
    DEFAULT_LONG_BREAK_1,
    DEFAULT_LONG_BREAK_2,
    DEFAULT_LUNCH_BREAK,
    DEFAULT_SCHOOL_START_TIME,
    DOMAIN
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

STEP_OPTIONS_DATA_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_LOOKAHEAD_WEEKS, default=DEFAULT_LOOKAHEAD_WEEKS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=4)
        ),
        vol.Optional("include_homework", default=True): bool,
        vol.Optional("include_exams", default=True): bool,
        vol.Optional("include_letters", default=True): bool,
        vol.Optional("include_grades", default=False): bool,
        # Schedule timing configuration
        vol.Optional(CONF_LESSON_DURATION, default=DEFAULT_LESSON_DURATION): vol.All(
            vol.Coerce(int), vol.Range(min=30, max=90)
        ),
        vol.Optional(CONF_SHORT_BREAK, default=DEFAULT_SHORT_BREAK): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=30)
        ),
        vol.Optional(CONF_LONG_BREAK_1, default=DEFAULT_LONG_BREAK_1): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=60)
        ),
        vol.Optional(CONF_LONG_BREAK_2, default=DEFAULT_LONG_BREAK_2): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=60)
        ),
        vol.Optional(CONF_LUNCH_BREAK, default=DEFAULT_LUNCH_BREAK): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=120)
        ),
        vol.Optional(CONF_SCHOOL_START_TIME, default=DEFAULT_SCHOOL_START_TIME): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = SchulmanagerAPI(data[CONF_EMAIL], data[CONF_PASSWORD], session)
    
    try:
        # Test authentication
        await api.authenticate()
        
        # Get students to validate account
        students = await api.get_students()
        
        if not students:
            raise SchulmanagerAPIError("No students found for this account")
        
        return {
            "title": f"Schulmanager ({data[CONF_EMAIL]})",
            "students": students,
        }
        
    except SchulmanagerAPIError as e:
        _LOGGER.error("Authentication failed: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("Unexpected error: %s", e)
        raise SchulmanagerAPIError(f"Unexpected error: {e}") from e


class SchulmanagerOnlineConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Schulmanager Online."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: Dict[str, Any] = {}
        self._students: list = []

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_input(self.hass, user_input)
        except SchulmanagerAPIError as e:
            if "401" in str(e) or "authentication" in str(e).lower():
                errors["base"] = "invalid_auth"
            elif "students" in str(e).lower():
                errors["base"] = "no_students"
            else:
                errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            # Store data for next step
            self._data = user_input
            self._students = info["students"]
            
            # Set unique ID based on email
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            
            # Show options step
            return await self.async_step_options()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_options(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the options step."""
        if user_input is None:
            return self.async_show_form(
                step_id="options", 
                data_schema=STEP_OPTIONS_DATA_SCHEMA,
                description_placeholders={
                    "students": ", ".join([
                        f"{s.get('firstname', '')} {s.get('lastname', '')}" 
                        for s in self._students
                    ])
                }
            )

        # Create the config entry
        return self.async_create_entry(
            title=f"Schulmanager ({self._data[CONF_EMAIL]})",
            data=self._data,
            options=user_input,
        )

    @staticmethod
    @config_entries.callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SchulmanagerOnlineOptionsFlow:
        """Create the options flow."""
        return SchulmanagerOnlineOptionsFlow(config_entry)


class SchulmanagerOnlineOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Schulmanager Online."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_options = self.config_entry.options
        
        options_schema = vol.Schema(
            {
                vol.Optional(
                    CONF_LOOKAHEAD_WEEKS,
                    default=current_options.get(CONF_LOOKAHEAD_WEEKS, DEFAULT_LOOKAHEAD_WEEKS)
                ): vol.All(vol.Coerce(int), vol.Range(min=1, max=4)),
                vol.Optional(
                    "include_homework",
                    default=current_options.get("include_homework", True)
                ): bool,
                vol.Optional(
                    "include_exams",
                    default=current_options.get("include_exams", True)
                ): bool,
                vol.Optional(
                    "include_grades",
                    default=current_options.get("include_grades", False)
                ): bool,
                # Schedule timing configuration
                vol.Optional(
                    CONF_LESSON_DURATION,
                    default=current_options.get(CONF_LESSON_DURATION, DEFAULT_LESSON_DURATION)
                ): vol.All(vol.Coerce(int), vol.Range(min=30, max=90)),
                vol.Optional(
                    CONF_SHORT_BREAK,
                    default=current_options.get(CONF_SHORT_BREAK, DEFAULT_SHORT_BREAK)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=30)),
                vol.Optional(
                    CONF_LONG_BREAK_1,
                    default=current_options.get(CONF_LONG_BREAK_1, DEFAULT_LONG_BREAK_1)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Optional(
                    CONF_LONG_BREAK_2,
                    default=current_options.get(CONF_LONG_BREAK_2, DEFAULT_LONG_BREAK_2)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=60)),
                vol.Optional(
                    CONF_LUNCH_BREAK,
                    default=current_options.get(CONF_LUNCH_BREAK, DEFAULT_LUNCH_BREAK)
                ): vol.All(vol.Coerce(int), vol.Range(min=0, max=120)),
                vol.Optional(
                    CONF_SCHOOL_START_TIME,
                    default=current_options.get(CONF_SCHOOL_START_TIME, DEFAULT_SCHOOL_START_TIME)
                ): str,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
