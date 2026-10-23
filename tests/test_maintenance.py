"""Offline maintenance regressions; real client code, synthetic HTTP/HA boundary.

Install aiohttp to run. The strict registry double models entry ownership and
identifier collision invariants; it is not a complete Home Assistant runtime.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
import importlib.util
import io
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "custom_components/schulmanager_online"
FIXTURES = Path(__file__).parent / "fixtures/bundle"
ORIGIN = "https://login.schulmanager-online.de/"
VERSION = "e3cf8c0506"


def load_modules():
    package = "_schulmanager_maintenance_tests"
    modules = {package: ModuleType(package)}
    modules[package].__path__ = [str(COMPONENT)]
    for name in ("homeassistant", "homeassistant.const", "homeassistant.helpers",
                 "homeassistant.helpers.device_registry"):
        modules[name] = ModuleType(name)
    modules["homeassistant.const"].Platform = SimpleNamespace(
        SENSOR="sensor", CALENDAR="calendar", BUTTON="button", TODO="todo"
    )
    dr = modules["homeassistant.helpers.device_registry"]
    dr.DeviceEntryType = SimpleNamespace(SERVICE="service")
    dr.DeviceRegistry = object
    loaded = []
    with patch.dict(sys.modules, modules):
        for name in ("const", "bundle", "api", "devices"):
            spec = importlib.util.spec_from_file_location(f"{package}.{name}", COMPONENT / f"{name}.py")
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            loaded.append(module)
    return loaded[1:]


bundle, api_module, devices = load_modules()


class Response:
    def __init__(self, body="", *, status=200, url=ORIGIN, data=None):
        self.body, self.status, self.url, self.data = body, status, url, data
        self.content = SimpleNamespace(read=AsyncMock(side_effect=io.BytesIO(body.encode()).read))

    async def __aenter__(self):
        self.content = SimpleNamespace(read=AsyncMock(side_effect=io.BytesIO(self.body.encode()).read))
        return self

    async def __aexit__(self, *args):
        return False

    async def text(self):
        return self.body

    async def json(self):
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


class Session:
    def __init__(self, resources=None, replies=()):
        self.resources = resources or {}
        self.replies = iter(replies)
        self.gets, self.posts = [], []

    def get(self, url, **kwargs):
        self.gets.append(url)
        value = self.resources.get(url, Response(status=404, url=url))
        if isinstance(value, Exception):
            raise value
        return value

    def post(self, url, **kwargs):
        self.posts.append((url, kwargs))
        return next(self.replies)


def real_fixture():
    return Session({
        ORIGIN: Response((FIXTURES / "index.html").read_text()),
        ORIGIN + "static/main-3NS7PKZO.js": Response((FIXTURES / "main.js").read_text(), url=ORIGIN + "static/main-3NS7PKZO.js"),
        ORIGIN + "static/chunk-VHWXMUR6.js": Response((FIXTURES / "api-chunk.js").read_text(), url=ORIGIN + "static/chunk-VHWXMUR6.js"),
    })


class BundleDiscoveryTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_public_fixture_and_imported_binding(self):
        session = real_fixture()
        self.assertEqual(await bundle.detect_bundle_version(session, ORIGIN), VERSION)
        self.assertIn(ORIGIN + "static/chunk-VHWXMUR6.js", session.gets)

    async def test_url_forms_redirect_document_base_and_duplicate_fetches(self):
        for reference, expected in (
            ("a.js", "https://cdn.example/app/a.js"),
            ("/a.js", "https://cdn.example/a.js"),
            ("https://static.example/a.js", "https://static.example/a.js"),
            ("//static.example/a.js", "https://static.example/a.js"),
        ):
            with self.subTest(reference=reference):
                session = Session({
                    ORIGIN: Response(f'<base href="/app/"><script src="{reference}"></script>', url="https://cdn.example/redirect/index"),
                    expected: Response('const p={bundleVersion:"123456789a"};', url=expected),
                })
                self.assertEqual(await bundle.detect_bundle_version(session, ORIGIN), "123456789a")
                self.assertEqual(session.gets, [ORIGIN, expected])

    async def test_js_redirect_controls_relative_imports_and_cycles_are_deduplicated(self):
        session = Session({
            ORIGIN: Response('<script src="main.js"></script><script src="main.js"></script>'),
            ORIGIN + "main.js": Response('import "./chunk.js";import("./chunk.js");', url="https://cdn.example/sub/main.js"),
            "https://cdn.example/sub/chunk.js": Response('import "./main.js"; const p={bundleVersion:"123456789a"};'),
        })
        self.assertEqual(await bundle.detect_bundle_version(session, ORIGIN), "123456789a")
        self.assertEqual(session.gets.count(ORIGIN + "main.js"), 1)
        self.assertEqual(session.gets.count("https://cdn.example/sub/chunk.js"), 1)

    def test_semantic_version_wins_over_unrelated_hashes(self):
        source = 'fetch("/api/calls");var hash="aaaaaaaaaa";var x="123456789a";var p={bundleVersion:x,requests:e};'
        self.assertEqual(bundle.version_in_source(source), "123456789a")
        self.assertIsNone(bundle.version_in_source('post("/api/calls", "3505280ee7");'))
        self.assertIsNone(bundle.version_in_source('var x="123456789a";x=other;var p={bundleVersion:x};'))
        self.assertIsNone(bundle.version_in_source('var p={bundleVersion:x};'))
        self.assertIsNone(bundle.version_in_source('var p={bundleVersion:"123456789a"};var q={bundleVersion:"aaaaaaaaaa"};'))
        self.assertEqual(bundle.version_in_source('var p={"bundleVersion":"123456789a"};'), "123456789a")

    async def test_empty_missing_http_error_timeout_and_bad_base_are_distinct(self):
        for response, expected in (
            (Response(""), "value detection"),
            (Response('<script src="main.js"></script>'), "JS fetch: HTTP 404"),
            (Response(status=503), "HTML fetch: HTTP 503"),
            (TimeoutError("private response"), "HTML fetch: TimeoutError"),
            (Response('<base href="javascript:bad">'), "resource resolution"),
        ):
            with self.subTest(expected=expected):
                with self.assertRaisesRegex(bundle.BundleDetectionError, expected):
                    await bundle.detect_bundle_version(Session({ORIGIN: response}), ORIGIN)

    async def test_resource_depth_count_size_and_total_time_limits(self):
        session = Session({ORIGIN: Response('<script src="main.js"></script>')})
        session.resources[ORIGIN + "main.js"] = Response('import "./next.js";', url=ORIGIN + "main.js")
        session.resources[ORIGIN + "next.js"] = Response('import "./third.js";', url=ORIGIN + "next.js")
        session.resources[ORIGIN + "third.js"] = Response('import "./too-deep.js";', url=ORIGIN + "third.js")
        with self.assertRaises(bundle.BundleDetectionError):
            await bundle.detect_bundle_version(session, ORIGIN)
        self.assertNotIn(ORIGIN + "too-deep.js", session.gets)
        with patch.object(bundle, "MAX_RESOURCES", 1):
            session.gets.clear()
            with self.assertRaises(bundle.BundleDetectionError):
                await bundle.detect_bundle_version(session, ORIGIN)
            self.assertEqual(len(session.gets), 2)  # HTML plus one JS resource
        with patch.object(bundle, "MAX_BYTES", 2):
            with self.assertRaisesRegex(bundle.BundleDetectionError, "size limit"):
                await bundle.detect_bundle_version(Session({ORIGIN: Response("long")}), ORIGIN)
        async def slow(*args):
            await asyncio.sleep(1)
        with patch.object(bundle, "fetch_source", side_effect=slow), patch.object(bundle, "DISCOVERY_TIMEOUT", 0.001):
            with self.assertRaisesRegex(bundle.BundleDetectionError, "discovery timeout"):
                await bundle.detect_bundle_version(session, ORIGIN)


class APIMaintenanceTests(unittest.IsolatedAsyncioTestCase):
    def client(self, replies=()):
        client = api_module.SchulmanagerAPI("private-email", "private-password", Session(replies=replies))
        client.token, client.token_expires = "private-token", datetime.now() + timedelta(hours=1)
        client._detect_bundle_version = AsyncMock(return_value=VERSION)
        client.authenticate = AsyncMock()
        return client

    async def test_discovery_cache_expiry_and_concurrent_cache_miss(self):
        client = self.client()
        self.assertEqual(await asyncio.gather(*(client._ensure_bundle_version() for _ in range(4))), [VERSION] * 4)
        client._detect_bundle_version.assert_awaited_once()
        self.assertEqual(client.bundle_version_source, "detected")
        client.bundle_version_expires = datetime.now() - timedelta(seconds=1)
        client._detect_bundle_version.return_value = "123456789a"
        self.assertEqual(await client._ensure_bundle_version(), "123456789a")
        self.assertEqual(client._detect_bundle_version.await_count, 2)

    async def test_failed_detection_keeps_last_success_and_short_failure_cache(self):
        client = self.client()
        client.last_successful_bundle_version = "123456789a"
        client._detect_bundle_version.side_effect = bundle.BundleDetectionError("HTML fetch: HTTP 503")
        with self.assertLogs(api_module._LOGGER, "WARNING") as logs:
            self.assertEqual(await client._ensure_bundle_version(), "123456789a")
        self.assertEqual(client.bundle_version_source, "last_api_success")
        self.assertEqual(await client._ensure_bundle_version(), "123456789a")
        client._detect_bundle_version.assert_awaited_once()
        self.assertLess(client.bundle_version_expires - datetime.now(), timedelta(minutes=6))
        self.assertIn("HTML fetch", logs.output[0])

    async def test_emergency_and_previous_detection_are_distinguished(self):
        for previous, expected, source in ((None, "3505280ee7", "emergency_fallback"),
                                           (VERSION, VERSION, "previous_detection")):
            client = self.client()
            client.bundle_version = previous
            client._detect_bundle_version.side_effect = bundle.BundleDetectionError("value detection")
            with self.assertLogs(api_module._LOGGER, "WARNING"):
                self.assertEqual(await client._ensure_bundle_version(), expected)
            self.assertEqual(client.bundle_version_source, source)
            self.assertIsNone(client.last_successful_bundle_version)

    async def test_http_nested_and_explicit_version_rejections_retry_once(self):
        success = {"results": [{"status": 200, "data": []}]}
        for first, expected_auth in (
            (Response(status=401, data=ValueError("private body")), 1),
            (Response(status=403, data={}), 1),
            (Response(data={"results": [{"status": 403}]}), 1),
            (Response(data={"responses": [{"status": 401}]}), 1),
            (Response(status=409, data={"code": "BUNDLE_VERSION_MISMATCH"}), 0),
        ):
            with self.subTest(status=first.status, data=first.data):
                client = self.client([first, Response(data=success)])
                client._detect_bundle_version.side_effect = ["123456789a", VERSION]
                with self.assertLogs(api_module._LOGGER, "WARNING"):
                    self.assertEqual(await client._make_api_call([{"private-student": "secret"}]), success)
                self.assertEqual(len(client.session.posts), 2)
                self.assertEqual(client.authenticate.await_count, expected_auth)
                self.assertEqual(client.last_successful_bundle_version, VERSION)
                self.assertEqual([p[1]["json"]["bundleVersion"] for p in client.session.posts], ["123456789a", VERSION])

    async def test_mixed_rejections_share_budget_and_do_not_confirm_failed_version(self):
        client = self.client([Response(status=401, data={}), Response(data={"results": [{"status": 403}]})])
        with self.assertLogs(api_module._LOGGER, "WARNING"):
            with self.assertRaises(api_module.SchulmanagerAPIError):
                await client._make_api_call([])
        self.assertEqual(len(client.session.posts), 2)
        self.assertIsNone(client.last_successful_bundle_version)

    async def test_normal_http_failure_json_error_and_server_timeout_do_not_retry(self):
        for reply in (Response(status=500, data={"error": "private-response"}),
                      Response(data=ValueError("private-json")), Response(data=[])):
            client = self.client([reply])
            with self.assertRaises(api_module.SchulmanagerAPIError) as err:
                await client._make_api_call([])
            self.assertNotIn("private", str(err.exception))
            self.assertEqual(len(client.session.posts), 1)
        client = self.client()
        client.session.post = Mock(side_effect=TimeoutError())
        with self.assertRaises(TimeoutError):
            await client._make_api_call([])
        self.assertEqual(client.session.post.call_count, 1)

    async def test_authentication_refresh_keeps_school_selection(self):
        client = self.client()
        client.token = None
        client.institution_id = 42
        await client._ensure_authenticated()
        client.authenticate.assert_awaited_once_with(institution_id=42)

    async def test_real_authentication_and_multi_school_login_paths(self):
        client = api_module.SchulmanagerAPI("synthetic-user", "synthetic-password", Session(replies=[
            Response(data={"salt": "synthetic-salt"}),
            Response(data={"jwt": "synthetic-token", "user": {"institutionId": 42}}),
        ]))
        client._generate_salted_hash = Mock(return_value="synthetic-hash")
        await client.authenticate(institution_id=42)
        self.assertEqual(client.token, "synthetic-token")
        self.assertEqual(client.institution_id, 42)
        self.assertGreater(client.token_expires, datetime.now())
        self.assertEqual([p[1]["json"]["institutionId"] for p in client.session.posts], [42, 42])
        client.session = Session(replies=[Response(data={"multipleAccounts": [{"id": 42}, {"id": 43}]})])
        await client._login("synthetic-hash")
        self.assertIsNone(client.token)
        self.assertEqual(len(client.get_multiple_accounts()), 2)

    async def test_schedule_cannot_add_a_second_nested_retry_budget(self):
        client = self.client([Response(status=401, data={}), Response(data={"results": [{"status": 403}]})])
        client.get_students = AsyncMock(return_value=[{"id": 42}])
        with self.assertLogs(api_module._LOGGER, "WARNING"):
            with self.assertRaises(api_module.SchulmanagerAPIError):
                await client.get_schedule(42, datetime.now().date(), datetime.now().date())
        self.assertEqual(len(client.session.posts), 2)

    async def test_logs_never_expose_request_headers_or_response_bodies(self):
        client = self.client([Response(data={"results": [{"status": 200, "data": "private-response"}]})])
        with self.assertLogs(api_module._LOGGER, "DEBUG") as logs:
            await client._make_api_call([{"student": "private-student"}])
        self.assertNotIn("private", " ".join(logs.output))


class Registry:
    """Entry-scoped strict public API; collisions fail instead of silently merging."""
    def __init__(self):
        self.entries = []

    def async_get_device_by_identifier(self, identifier, config_entry_id):
        return next((d for d in self.entries if d.config_entry_id == config_entry_id and identifier in d.identifiers), None)

    def async_get_or_create(self, *, config_entry_id, identifiers, name, manufacturer, model,
                            via_device_id=None, entry_type=None):
        matches = [d for d in self.entries if d.config_entry_id == config_entry_id and d.identifiers & identifiers]
        assert len(matches) <= 1, "Unsafe collision reconciliation"
        if not matches:
            device = SimpleNamespace(id=f"device-{len(self.entries)}", config_entry_id=config_entry_id,
                                     identifiers=set(), area_id=None, name_by_user=None,
                                     disabled_by=None, labels=set(), config_subentry_id=None)
            self.entries.append(device)
        else:
            device = matches[0]
        device.identifiers |= identifiers
        device.name, device.via_device_id = name, via_device_id
        return device


class DeviceMaintenanceTests(unittest.TestCase):
    student = {"id": 42, "firstname": "Synthetic", "lastname": "Student"}

    def test_fresh_setup_links_service_and_reload_is_idempotent(self):
        registry = Registry()
        for _ in range(3):
            devices.async_register_devices(registry, "entry-a", [self.student])
        self.assertEqual(len(registry.entries), 2)
        service, student = registry.entries
        self.assertEqual(student.via_device_id, service.id)
        self.assertEqual(student.identifiers, {("schulmanager_online", "42"), ("schulmanager_online", "student_42")})

    def test_old_new_and_both_identifiers_keep_ids_and_user_assignments(self):
        for identifiers in ({"42"}, {"student_42"}, {"42", "student_42"}):
            with self.subTest(identifiers=identifiers):
                registry = Registry()
                old = registry.async_get_or_create(config_entry_id="entry-a", identifiers={("schulmanager_online", x) for x in identifiers},
                                                  name="Original", manufacturer="", model="")
                old.area_id, old.name_by_user, old.labels = "room", "Chosen name", {"family"}
                old.disabled_by = "user"
                for _ in range(2):
                    devices.async_register_devices(registry, "entry-a", [self.student])
                self.assertIs(registry.async_get_device_by_identifier(("schulmanager_online", "42"), "entry-a"), old)
                self.assertEqual((old.area_id, old.name_by_user, old.labels, old.disabled_by), ("room", "Chosen name", {"family"}, "user"))
                self.assertEqual(len(registry.entries), 2)

    def test_same_student_id_in_two_entries_is_not_shared(self):
        registry = Registry()
        for entry in ("entry-a", "entry-b", "entry-a", "entry-b"):
            devices.async_register_devices(registry, entry, [self.student])
        self.assertEqual(len(registry.entries), 4)
        a = registry.async_get_device_by_identifier(("schulmanager_online", "42"), "entry-a")
        b = registry.async_get_device_by_identifier(("schulmanager_online", "42"), "entry-b")
        self.assertNotEqual(a.id, b.id)
        self.assertNotEqual(a.via_device_id, b.via_device_id)

    def test_separate_legacy_device_is_preserved_with_all_links(self):
        registry = Registry()
        current = registry.async_get_or_create(config_entry_id="entry-a", identifiers={("schulmanager_online", "42")}, name="Current", manufacturer="", model="")
        legacy = registry.async_get_or_create(config_entry_id="entry-a", identifiers={("schulmanager_online", "student_42")}, name="Legacy", manufacturer="", model="")
        legacy.area_id, legacy.name_by_user, legacy.config_subentry_id = "room", "Keep", "subentry"
        legacy.entities = [{"disabled_by": "user"}]
        legacy.children = ["dependent-device"]
        before = vars(legacy).copy()
        with self.assertLogs(devices._LOGGER, "WARNING"):
            for _ in range(2):
                devices.async_register_devices(registry, "entry-a", [self.student])
        self.assertEqual(len(registry.entries), 3)
        self.assertEqual(vars(legacy), before)
        self.assertEqual(current.identifiers, {("schulmanager_online", "42")})
