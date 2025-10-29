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
    DOMAIN,
    OPT_SCHEDULE_HIGHLIGHT,
    OPT_SCHEDULE_HIDE_CANCELLED_NO_HIGHLIGHT,
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
        vol.Optional(OPT_SCHEDULE_HIGHLIGHT, default=True): bool,
        vol.Optional(OPT_SCHEDULE_HIDE_CANCELLED_NO_HIGHLIGHT, default=False): bool,
        # NOTE: Schedule timing configuration removed - API provides class hours
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    api = SchulmanagerAPI(data[CONF_EMAIL], data[CONF_PASSWORD], session)
    
    try:
        # Test authentication
        await api.authenticate()
        
        # Check if this is a multi-school account
        multiple_accounts = api.get_multiple_accounts()
        if multiple_accounts:
            # Multi-school account detected - collect students from ALL schools
            _LOGGER.info("Multi-school account detected with %d schools", len(multiple_accounts))
            
            all_students = []
            schools = []
            
            # Iterate over all schools and collect students
            for school in multiple_accounts:
                school_id = school.get("id")
                school_name = school.get("label", f"School {school_id}")
                
                if not school_id:
                    _LOGGER.warning("Skipping school with no ID: %s", school)
                    continue
                
                try:
                    _LOGGER.info("Collecting students from school: %s (ID: %d)", school_name, school_id)
                    
                    # Create new API instance for this school
                    school_api = SchulmanagerAPI(data[CONF_EMAIL], data[CONF_PASSWORD], session)
                    await school_api.authenticate(institution_id=school_id)
                    
                    # Get students from this school
                    school_students = await school_api.get_students()
                    
                    _LOGGER.info("Found %d students in %s", len(school_students), school_name)
                    
                    # Fetch detailed institution info for this school
                    institution_name_short = school_name
                    institution_city = ""
                    institution_address = ""
                    
                    try:
                        institution_data = await school_api.get_institution()
                        raw_name = institution_data.get("name", school_name)
                        city = institution_data.get("city", "")
                        street = institution_data.get("street", "")
                        zipcode = institution_data.get("zipcode", "")
                        
                        # Build institution_name with separator if city is in the name
                        if city and city in raw_name:
                            institution_name_short = raw_name.replace(city, "").strip()
                            school_name = f"{institution_name_short} | {city}"
                        else:
                            school_name = raw_name
                            institution_name_short = raw_name
                        
                        institution_city = city
                        
                        # Build full address
                        if street and zipcode and city:
                            institution_address = f"{street}, {zipcode} {city}"
                        elif street and city:
                            institution_address = f"{street}, {city}"
                        elif city:
                            institution_address = city
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
                    
                    # Store school info
                    schools.append({
                        "id": school_id,
                        "name": school_name
                    })
                    
                except Exception as e:
                    _LOGGER.error("Failed to get students from school %s (ID: %d): %s", 
                                school_name, school_id, e)
                    # Continue with other schools even if one fails
                    continue
            
            if not all_students:
                raise SchulmanagerAPIError("No students found across any schools for this account")
            
            _LOGGER.info("Total students collected from all schools: %d", len(all_students))
            
            return {
                "title": f"Schulmanager ({data[CONF_EMAIL]})",
                "students": all_students,
                "schools": schools,
                "multi_school": True,
            }
        
        # Single school account - get students to validate
        students = await api.get_students()
        
        if not students:
            raise SchulmanagerAPIError("No students found for this account")
        
        # For single-school accounts, fetch institution details from API
        institution_name = f"School {api.institution_id}"  # Fallback
        institution_name_short = institution_name
        institution_city = ""
        institution_address = ""
        
        if api.institution_id:
            try:
                # Fetch full institution details using the get-institution endpoint
                institution_data = await api.get_institution()
                
                # Extract all institution fields
                raw_name = institution_data.get("name", institution_name)
                city = institution_data.get("city", "")
                street = institution_data.get("street", "")
                zipcode = institution_data.get("zipcode", "")
                
                # Build institution_name with separator if city is in the name
                if city and city in raw_name:
                    # Remove city from the end of the name and add separator
                    institution_name_short = raw_name.replace(city, "").strip()
                    institution_name = f"{institution_name_short} | {city}"
                else:
                    institution_name = raw_name
                    institution_name_short = raw_name
                
                institution_city = city
                
                # Build full address
                if street and zipcode and city:
                    institution_address = f"{street}, {zipcode} {city}"
                elif street and city:
                    institution_address = f"{street}, {city}"
                elif city:
                    institution_address = city
                
                _LOGGER.info("✅ Retrieved institution: %s", institution_name)
            except Exception as e:
                _LOGGER.warning("Could not fetch institution details: %s (using fallback)", e)
            
            # Add institution info to each student
            for student in students:
                student["_institution_id"] = api.institution_id
                student["_institution_name"] = institution_name
                student["_institution_name_short"] = institution_name_short
                student["_institution_city"] = institution_city
                student["_institution_address"] = institution_address
        
        return {
            "title": f"Schulmanager ({data[CONF_EMAIL]})",
            "students": students,
            "schools": [{"id": api.institution_id, "name": institution_name}] if api.institution_id else [],
            "multi_school": False,
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
        self._schools: list[Dict[str, Any]] = []

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
        except Exception as e:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception during config flow: %s", str(e))
            # Provide more helpful error messages for common cases
            if "timeout" in str(e).lower():
                errors["base"] = "timeout"
            elif "json" in str(e).lower() or "decode" in str(e).lower():
                errors["base"] = "invalid_response"
            else:
                errors["base"] = "unknown"
                # Log the exception type to help debugging
                _LOGGER.error("Exception type: %s", type(e).__name__)
        else:
            # Store data for next step
            self._data = user_input
            self._students = info.get("students", [])
            self._schools = info.get("schools", [])
            
            # Store schools data in config entry data
            if self._schools:
                self._data["schools"] = self._schools
                _LOGGER.info("Storing %d school(s) in config entry", len(self._schools))
            
            # Log multi-school info
            if info.get("multi_school", False):
                _LOGGER.info("Multi-school account setup completed with %d students from %d schools", 
                            len(self._students), len(self._schools))

            # Set unique ID based on email
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            self._abort_if_unique_id_configured()
            
            # Show options step
            return await self.async_step_options()
        
        # If there were errors, show the form again
        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_options(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the options step."""
        if user_input is None:
            # Build student list with school names for multi-school accounts
            student_list = []
            for s in self._students:
                name = f"{s.get('firstname', '')} {s.get('lastname', '')}"
                school = s.get('_institution_name')
                if school:
                    student_list.append(f"{name} ({school})")
                else:
                    student_list.append(name)
            
            return self.async_show_form(
                step_id="options", 
                data_schema=STEP_OPTIONS_DATA_SCHEMA,
                description_placeholders={
                    "students": ", ".join(student_list)
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
        # Store entry internally; do not set self.config_entry (deprecated)
        self._entry = config_entry

    async def async_step_init(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current options
        current_options = self._entry.options
        
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
                    "include_letters",
                    default=current_options.get("include_letters", True)
                ): bool,
                vol.Optional(
                    "include_grades",
                    default=current_options.get("include_grades", False)
                ): bool,
                vol.Optional(
                    OPT_SCHEDULE_HIGHLIGHT,
                    default=current_options.get(OPT_SCHEDULE_HIGHLIGHT, True)
                ): bool,
                vol.Optional(
                    OPT_SCHEDULE_HIDE_CANCELLED_NO_HIGHLIGHT,
                    default=current_options.get(OPT_SCHEDULE_HIDE_CANCELLED_NO_HIGHLIGHT, False)
                ): bool,
                # NOTE: Schedule timing configuration removed - API provides class hours
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=options_schema,
        )
