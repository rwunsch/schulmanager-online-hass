"""Offline calendar regressions using synthetic lessons and a minimal HA surface.

Import the actual calendar module, constants and free-hour helpers. Only HA's
entity/event types and the coordinator import are replaced; these are unit
tests, not a running Home Assistant integration test.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import Mock, patch


PACKAGE_PATH = Path(__file__).resolve().parents[1] / "custom_components" / "schulmanager_online"


def load_calendar():
    """Keep the HA stubs private so existing sensor tests remain independent."""
    package_name = "_schulmanager_calendar_tests"
    package = types.ModuleType(package_name)
    package.__path__ = [str(PACKAGE_PATH)]
    modules = {package_name: package}
    for name in (
        "homeassistant", "homeassistant.components", "homeassistant.components.calendar",
        "homeassistant.config_entries", "homeassistant.const", "homeassistant.core",
        "homeassistant.helpers", "homeassistant.helpers.entity_platform",
        "homeassistant.helpers.update_coordinator", f"{package_name}.coordinator",
    ):
        modules[name] = types.ModuleType(name)

    @dataclass
    class CalendarEvent:
        start: datetime
        end: datetime
        summary: str
        description: str

    class CalendarEntity:
        pass

    class CoordinatorEntity:
        def __init__(self, coordinator):
            self.coordinator = coordinator

    modules["homeassistant.components.calendar"].CalendarEntity = CalendarEntity
    modules["homeassistant.components.calendar"].CalendarEvent = CalendarEvent
    modules["homeassistant.config_entries"].ConfigEntry = object
    modules["homeassistant.const"].Platform = types.SimpleNamespace(
        SENSOR="sensor", CALENDAR="calendar", BUTTON="button", TODO="todo"
    )
    modules["homeassistant.core"].HomeAssistant = object
    modules["homeassistant.helpers.entity_platform"].AddEntitiesCallback = object
    modules["homeassistant.helpers.update_coordinator"].CoordinatorEntity = CoordinatorEntity
    modules[f"{package_name}.coordinator"].SchulmanagerDataUpdateCoordinator = object
    spec = importlib.util.spec_from_file_location(f"{package_name}.calendar", PACKAGE_PATH / "calendar.py")
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, modules):
        spec.loader.exec_module(module)
    return module


class CalendarRegressionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = load_calendar()

    def setUp(self):
        self.coordinator = Mock()
        self.coordinator.config_entry.options = {}
        self.coordinator.data = {
            "class_hours": [{"number": 2, "from": "09:10:00", "until": "09:55:00"}]
        }
        self.calendar = self.module.SchulmanagerOnlineCalendar(
            self.coordinator, student_id=1, student_name="Test Student", calendar_type="schedule"
        )
        self.start = datetime(2026, 10, 22, tzinfo=self.module.TIMEZONE)
        self.end = datetime(2026, 10, 23, tzinfo=self.module.TIMEZONE)
        self.logger = patch.object(self.module, "_LOGGER").start()
        self.addCleanup(patch.stopall)

    def tearDown(self):
        self.logger.warning.assert_not_called()
        self.logger.error.assert_not_called()

    def lesson(self, **overrides):
        result = {
            "date": "2026-10-22", "subject": "Mathematics", "room": "R101",
            "class_hour_number": 2, "classHour": {"number": 2},
            "type": "regularLesson", "teachers": [{"name": "Test Teacher"}],
        }
        result.update(overrides)
        return result

    def events(self, lessons):
        self.coordinator.get_student_data.return_value = {"schedule": lessons}
        return asyncio.run(self.calendar.async_get_events(None, self.start, self.end))

    def test_subject_fallbacks_create_events_with_and_without_room(self):
        for fields, expected in (
            ({"subject": None}, "Lesson"),
            ({"subject": None, "subject_name": "Robotics"}, "Robotics"),
            ({"subject": None, "subject_name": None}, "Lesson"),
            ({"subject": "", "subject_name": "Robotics"}, "Robotics"),
            ({"subject": "", "subject_name": ""}, "Lesson"),
            ({"subject": "Mathematics", "subject_name": "Other"}, "Mathematics"),
        ):
            for room in ("R101", ""):
                with self.subTest(fields=fields, room=room):
                    events = self.events([self.lesson(**fields, room=room)])
                    self.assertEqual(len(events), 1)
                    event = events[0]
                    self.assertEqual(event.summary, expected + (f" ({room})" if room else ""))
                    self.assertIn(f"Subject: {expected}", event.description)
                    self.assertIn("Class Hour: 2", event.description)

    def test_missing_subject_key_uses_name_or_default(self):
        for name, expected in (("Robotics", "Robotics"), (None, "Lesson")):
            with self.subTest(name=name):
                lesson = self.lesson(subject_name=name)
                del lesson["subject"]
                event = self.calendar._create_lesson_event(lesson)
                self.assertIsNotNone(event)
                self.assertEqual(event.summary, f"{expected} (R101)")

    def test_unnumbered_lessons_keep_actual_times_and_omit_class_hour(self):
        for hour in (None, "", "missing"):
            with self.subTest(hour=hour):
                lesson = self.lesson(
                    subject=None, subject_name="Robotics AG", class_hour_number=hour,
                    classHour={}, start_time="14:17:00", end_time="15:42:00",
                )
                if hour == "missing":
                    del lesson["class_hour_number"]
                with patch.object(self.calendar, "_get_configurable_class_times") as times:
                    events = self.events([lesson])
                    times.assert_not_called()
                self.assertEqual(len(events), 1)
                event = events[0]
                self.assertEqual(event.summary, "Robotics AG (R101)")
                self.assertEqual(event.start, self.start.replace(hour=14, minute=17))
                self.assertEqual(event.end, self.start.replace(hour=15, minute=42))
                self.assertNotIn("Class Hour:", event.description)

    def test_numbered_lessons_use_api_class_times(self):
        for hour in (2, "2"):
            with self.subTest(hour=hour):
                event = self.calendar._create_lesson_event(self.lesson(
                    class_hour_number=hour, start_time="14:00:00", end_time="15:00:00"
                ))
                self.assertIsNotNone(event)
                self.assertEqual(event.start, self.start.replace(hour=9, minute=10))
                self.assertEqual(event.end, self.start.replace(hour=9, minute=55))
                self.assertIn("Class Hour: 2", event.description)
                self.assertIn("Teacher: Test Teacher", event.description)

    def test_unnumbered_named_lesson_does_not_drop_event(self):
        event = self.calendar._create_lesson_event(self.lesson(
            subject="Robotics AG", class_hour_number=None,
            start_time="14:17:00", end_time="15:42:00",
        ))
        self.assertIsNotNone(event)
        self.assertEqual(event.start, self.start.replace(hour=14, minute=17))
        self.assertEqual(event.end, self.start.replace(hour=15, minute=42))
        self.assertNotIn("Class Hour:", event.description)

    def test_substitutions_and_cancellations_preserve_highlighting(self):
        for fields, highlighted, plain in (
            ({"type": "substitution"}, "🔄 Lesson (R101)", "Lesson (R101)"),
            ({"is_substitution": True}, "🔄 Lesson (R101)", "Lesson (R101)"),
            ({"type": "cancelledLesson"}, "❌ Lesson (Cancelled) (R101)", "X Lesson (Cancelled) (R101)"),
        ):
            for highlight, expected in ((True, highlighted), (False, plain)):
                with self.subTest(fields=fields, highlight=highlight):
                    self.coordinator.config_entry.options = {self.module.OPT_SCHEDULE_HIGHLIGHT: highlight}
                    events = self.events([self.lesson(subject=None, **fields)])
                    self.assertEqual(len(events), 1)
                    self.assertEqual(events[0].summary, expected)

    def test_replacement_wins_over_cancellation_regardless_of_order(self):
        cancelled = self.lesson(type="cancelledLesson")
        replacement = self.lesson(subject=None, subject_name="Robotics", type="substitution")
        for lessons in ([cancelled, replacement], [replacement, cancelled]):
            with self.subTest(cancelled_first=lessons[0] is cancelled):
                events = self.events(lessons)
                self.assertEqual(len(events), 1)
                self.assertEqual(events[0].summary, "🔄 Robotics (R101)")

    def test_cancelled_only_group_is_deduplicated_and_can_be_hidden(self):
        lessons = [self.lesson(type="cancelledLesson")] * 2
        self.assertEqual(len(self.events(lessons)), 1)
        self.coordinator.config_entry.options = {
            self.module.OPT_SCHEDULE_HIGHLIGHT: False,
            self.module.OPT_SCHEDULE_HIDE_CANCELLED_NO_HIGHLIGHT: True,
        }
        self.assertEqual(self.events(lessons), [])

    def test_unnumbered_lessons_at_different_times_are_both_returned(self):
        lessons = [self.lesson(
            subject=None, class_hour_number=None, classHour={},
            start_time=start, end_time=end,
        ) for start, end in (("14:17:00", "15:00:00"), ("15:10:00", "15:42:00"))]
        events = self.events(list(reversed(lessons)))
        self.assertEqual(len(events), 2)
        self.assertEqual([event.start.hour for event in events], [14, 15])

    def test_free_hours_and_out_of_range_lessons_are_excluded(self):
        for fields in ({"type": "freeHour"}, {"is_free_hour": True}, {"date": "2026-10-24"}):
            with self.subTest(fields=fields):
                self.assertEqual(self.events([self.lesson(**fields)]), [])


if __name__ == "__main__":
    unittest.main()
