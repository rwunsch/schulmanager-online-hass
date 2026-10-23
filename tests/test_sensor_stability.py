"""Stability tests for Schulmanager Online sensor helpers."""
from __future__ import annotations

import asyncio
import importlib
import sys
import types
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock
from zoneinfo import ZoneInfo


REPO_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_NAME = "custom_components.schulmanager_online"
PACKAGE_PATH = REPO_ROOT / "custom_components" / "schulmanager_online"


def _install_namespace_package() -> None:
    """Load integration modules without executing the HA package __init__."""
    custom_components = sys.modules.setdefault(
        "custom_components", types.ModuleType("custom_components")
    )
    custom_components.__path__ = [str(REPO_ROOT / "custom_components")]

    package = types.ModuleType(PACKAGE_NAME)
    package.__path__ = [str(PACKAGE_PATH)]
    sys.modules[PACKAGE_NAME] = package


def _install_homeassistant_stubs() -> None:
    """Install the small HA surface needed to import the coordinator."""
    homeassistant = sys.modules.setdefault("homeassistant", types.ModuleType("homeassistant"))

    const = types.ModuleType("homeassistant.const")

    class Platform:
        SENSOR = "sensor"
        CALENDAR = "calendar"
        BUTTON = "button"
        TODO = "todo"

    const.Platform = Platform
    sys.modules["homeassistant.const"] = const
    homeassistant.const = const

    core = types.ModuleType("homeassistant.core")
    core.HomeAssistant = object
    sys.modules["homeassistant.core"] = core
    homeassistant.core = core

    util = types.ModuleType("homeassistant.util")
    dt = types.ModuleType("homeassistant.util.dt")
    dt.now = lambda: datetime.now(ZoneInfo("Europe/Berlin"))
    util.dt = dt
    sys.modules["homeassistant.util"] = util
    sys.modules["homeassistant.util.dt"] = dt
    homeassistant.util = util

    helpers = types.ModuleType("homeassistant.helpers")
    sys.modules["homeassistant.helpers"] = helpers
    homeassistant.helpers = helpers

    update_coordinator = types.ModuleType("homeassistant.helpers.update_coordinator")

    class DataUpdateCoordinator:
        def __init__(self, hass, logger, name, update_interval):
            self.hass = hass
            self.logger = logger
            self.name = name
            self.update_interval = update_interval
            self.data = None

    class UpdateFailed(Exception):
        pass

    update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
    update_coordinator.UpdateFailed = UpdateFailed
    sys.modules["homeassistant.helpers.update_coordinator"] = update_coordinator
    helpers.update_coordinator = update_coordinator


_install_namespace_package()
_install_homeassistant_stubs()
schedule_sensors = importlib.import_module(f"{PACKAGE_NAME}.schedule_sensors")
exam_sensors = importlib.import_module(f"{PACKAGE_NAME}.exam_sensors")


class SensorHelperStabilityTest(unittest.TestCase):
    """Verify public sensor attributes keep stable shapes."""

    def test_schedule_attributes_use_empty_lists_for_missing_data(self):
        for value in ({}, {"next_school_day": None}, {"next_school_day": "unavailable"}):
            attributes = schedule_sensors.get_next_school_day_lessons_attributes(value)
            self.assertEqual(attributes["lessons"], [])
            self.assertEqual(attributes["lessons_by_hour"], {})
            self.assertEqual(attributes["subjects"], [])
            self.assertEqual(attributes["teachers"], [])

    def test_week_attributes_ignore_non_list_values(self):
        attributes = schedule_sensors.get_this_week_attributes({"this_week": "unknown"})
        self.assertEqual(attributes["lessons"], [])
        self.assertEqual(attributes["lessons_by_day"], {})

        attributes = schedule_sensors.get_next_week_attributes({"next_week": None})
        self.assertEqual(attributes["lessons"], [])
        self.assertEqual(attributes["lessons_by_day"], {})

    def test_changes_detected_handles_unknown_and_partial_fields(self):
        attributes = schedule_sensors.get_changes_detected_attributes(
            {"changes_detected": "unavailable"}
        )
        self.assertEqual(attributes["changes"], [])
        self.assertEqual(attributes["has_changes"], False)

        attributes = schedule_sensors.get_changes_detected_attributes(
            {
                "changes_detected": {
                    "has_changes": True,
                    "change_count": 1,
                    "changes": [None, {"type": "modified", "field_changes": [None]}],
                }
            }
        )
        self.assertEqual(len(attributes["changes"]), 1)
        self.assertEqual(attributes["changes"][0]["type"], "modified")

    def test_exams_upcoming_handles_empty_and_unavailable_data(self):
        for value in ({}, {"exams": None}, {"exams": "unknown"}):
            attributes = exam_sensors.get_exams_upcoming_attributes(value)
            self.assertEqual(attributes["exams"], [])
            self.assertEqual(attributes["subjects"], [])
            self.assertEqual(attributes["count"], 0)
            self.assertEqual(attributes["next_exam_date"], "")

    def test_exams_upcoming_normal_data(self):
        upcoming_date = (datetime.now().date() + timedelta(days=1)).isoformat()
        attributes = exam_sensors.get_exams_upcoming_attributes(
            {
                "exams": {
                    "data": [
                        {
                            "date": upcoming_date,
                            "subject": {"name": "Mathematik", "abbreviation": "M"},
                            "type": {"name": "Test"},
                        }
                    ]
                }
            }
        )
        self.assertEqual(attributes["count"], 1)
        self.assertEqual(attributes["exams"][0]["subject"], "Mathematik")
        self.assertTrue(attributes["exams"][0]["is_next_exam"])


class CoordinatorFallbackTest(unittest.IsolatedAsyncioTestCase):
    """Verify coordinator fallback data stays stable after API failures."""

    @classmethod
    def setUpClass(cls):
        _install_homeassistant_stubs()
        api_stub = types.ModuleType(f"{PACKAGE_NAME}.api")

        class SchulmanagerAPI:
            pass

        class SchulmanagerAPIError(Exception):
            pass

        api_stub.SchulmanagerAPI = SchulmanagerAPI
        api_stub.SchulmanagerAPIError = SchulmanagerAPIError
        sys.modules[f"{PACKAGE_NAME}.api"] = api_stub

        cls.coordinator_module = importlib.import_module(f"{PACKAGE_NAME}.coordinator")
        cls.api_module = importlib.import_module(f"{PACKAGE_NAME}.api")

    async def test_reuses_last_successful_data_after_timeout(self):
        coordinator = self.coordinator_module.SchulmanagerDataUpdateCoordinator(
            hass=Mock(),
            api_instances={1: Mock(get_schedule=AsyncMock())},
            options={"include_homework": False, "include_exams": False, "include_letters": False},
        )
        student = {"id": 1, "firstname": "Ada", "lastname": "Lovelace"}
        coordinator.students = [student]
        coordinator._last_successful_student_data[1] = {
            "info": student,
            "schedule": [{"date": "2999-01-01", "class_hour_number": 1}],
            "current_lesson": None,
            "next_lesson": None,
            "today_lessons": [],
            "today_changes": [],
            "tomorrow_lessons": [],
            "next_school_day": [],
            "this_week": [],
            "next_week": [],
            "changes_detected": {"has_changes": False, "changes": [], "change_count": 0},
            "homework": {"homeworks": []},
            "grades": {"grades": []},
            "exams": {"exams": [], "data": []},
            "_data_status": "loaded",
            "_last_error": "",
        }

        api = coordinator.api_instances[1]
        api.get_schedule.side_effect = asyncio.TimeoutError("timeout")

        data = await coordinator._async_update_data()
        student_data = data["students"][1]

        self.assertEqual(student_data["_data_status"], "stale")
        self.assertIn("timeout", student_data["_last_error"])
        self.assertEqual(student_data["schedule"], [{"date": "2999-01-01", "class_hour_number": 1}])
        self.assertEqual(student_data["changes_detected"]["changes"], [])

    async def test_uses_empty_defaults_after_authentication_error_without_previous_data(self):
        coordinator = self.coordinator_module.SchulmanagerDataUpdateCoordinator(
            hass=Mock(),
            api_instances={1: Mock(get_schedule=AsyncMock())},
            options={"include_homework": False, "include_exams": False, "include_letters": False},
        )
        student = {"id": 2, "firstname": "Grace", "lastname": "Hopper"}
        coordinator.students = [student]

        api = coordinator.api_instances[1]
        api.get_schedule.side_effect = self.api_module.SchulmanagerAPIError("bad auth")

        data = await coordinator._async_update_data()
        student_data = data["students"][2]

        self.assertEqual(student_data["_data_status"], "not_loaded")
        self.assertEqual(student_data["schedule"], [])
        self.assertEqual(student_data["next_school_day"], [])
        self.assertEqual(student_data["changes_detected"]["changes"], [])
        self.assertEqual(student_data["exams"]["data"], [])


if __name__ == "__main__":
    unittest.main()
