# Schulmanager maintenance — 1.3.1

## Scope and compatibility

Continues from released 1.3.0 and the merged `origin/main` at `828af2d`, keeping
the existing calendar/AG fixes and dashboard extensions. Work is in the
`HA Schulmanager/schulmanager-online-hass` checkout, not its parent Codex folder.
The unrelated local `schule.yaml` is not part of this release.

Minimum supported HA is **2026.10.0**, declared in `hacs.json`. Registry method
signatures were checked against official Core 2026.10.2 source. This deliberately
replaces the old 2024.1 compatibility claim; there is no deprecated-API fallback.
The unsupported manifest `homeassistant` key and redundant explicit `aiohttp`
requirement are removed; aiohttp is supplied by Home Assistant.

## Device registration

`async_get_device_by_identifier(identifier, config_entry_id)` looks up each alias
separately. Registration links to the returned service device's `.id` using
`via_device_id`. An existing device with old, new or both identifiers keeps its
ID and aliases. User-assigned name, area, labels and disabled state are not set.
Entity IDs and unique IDs are unchanged.

If old and new aliases already belong to separate devices, preserve both and
warn rather than submit colliding identifiers to HA's automatic reconciliation.
This intentionally leaves ambiguous legacy records for manual review. It does
not silently merge their entities or metadata. The former deletion path is
removed entirely: no entity-only emptiness test, owner transfer, child-device
cleanup or broad exception swallowing. HA's actual entity helper is the module
function `er.async_entries_for_device(registry, device_id, include_disabled_entities=True)`,
not the instance method previously used; registration no longer needs it.

## Bundle discovery and failure policy

The public entrypoint remains `https://login.schulmanager-online.de/`. Its main
module imports another module containing both a unique version binding and the
`bundleVersion` request property. The previous detector did not follow imports.
The public, minimal [fixtures](../tests/fixtures/bundle/README.md) preserve this
chain; no student/account data is included. The old 1.3.0 client reproduces the
fallback on the same fixture; the new code discovers the payload's version.

Resolution uses the redirected document URL, first HTML base and redirected JS
resource URL. Initial HTML scripts/module preloads may reference a CDN; imported
resources stay on their parent origin. Ordering is deterministic, duplicate URLs
are skipped, and only literal JS imports are followed. Limits: 96 JS resources,
two import levels, 4 MiB per resource, five seconds per fetch, 30 seconds overall.
There is no JavaScript evaluation or general recursive crawler.

Only an explicit `bundleVersion` literal or a unique same-file literal binding
used in that property qualifies. Unrelated hashes near `post` or `fetch`, file
hashes, ambiguous assignments and unresolved bindings do not qualify. This is
a constrained static recognizer, not a general JavaScript parser; future web-app
syntax changes can still require a parser update.

Successful discovery is cached for one hour, serialized per API instance. On
failure, retry discovery after five minutes and use, in order: last successfully
API-used version, previous detected version, historical emergency `3505280ee7`.
These sources are reported separately in diagnostics. An emergency value is
never reported as a successful discovery; last-successful values survive a
failed discovery. Cache/last-success state is in memory and resets on restart.

HTTP and nested 401/403, and explicit bundle-version conflict messages, share
one retry budget (at most two posts per logical call). The retry refreshes public
discovery and, for authentication rejection, the selected school's login.
The schedule method cannot add another retry loop. Ordinary HTTP failures and
timeouts are not retried. Logs in the affected request path contain statuses,
counts and stage diagnostics, not bearer headers, full payloads or responses.

## Verification and operations

Run `python -m pip install aiohttp`, then
`python -m unittest discover -s tests -v` and
`python -m compileall -q custom_components/schulmanager_online tests`.
Maintenance tests execute actual client/device helper code with a strict,
entry-scoped registry double and synthetic HTTP; they are not a full HA runtime.
All **37 tests pass** on Python 3.14.6, including the ten retained calendar
regressions, seven retained sensor/coordinator regressions and twenty maintenance
regressions. Compilation and `git diff --check` pass. The unchanged 1.3.0
detector reproduces the historical fallback on the fixture, and the unchanged
registry block fails against the strict API boundary (its broad exception handler
swallows the rejected `via_device` call). The new public-source discovery also
returned `e3cf8c0506` against the complete live website in about one second on
23 October. Live HA validation is recorded separately after deployment.

The historic `deploy.sh` and interactive `release.sh` still encode obsolete
paths/assumptions and are not used. Deployment follows the prior SSH workflow:
verify exact current source, back up changed files outside web-served paths,
stage and verify replacement hashes, replace only owned integration files,
run `ha core check`, restart Core once to import the changed Python modules,
then compare registries, diagnostics, fresh sensor/calendar data and only new
logs. A config-entry reload alone cannot activate changed imported Python code.

Official references:

- https://contributors.home-assistant.io/blog/2026/08/24/device-registry-follow-up-changes/
- https://raw.githubusercontent.com/home-assistant/core/2026.10.2/homeassistant/helpers/device_registry.py
- https://raw.githubusercontent.com/home-assistant/core/2026.10.2/homeassistant/helpers/entity_registry.py

## Live acceptance — 23 October 2026

Implementation commit: `74ae9e3ffb46fcffbb3b72e4d0010bc1c9253b3a`.
Release PR: https://github.com/tkarle/schulmanager-online-hass/pull/3.

Target: HA Core **2026.10.2**, `/config/custom_components/schulmanager_online`.
The installed baseline was 1.2.2; all 33 live files matched that tag before changes.
The release includes the 1.3.0 README and changes only seven integration files:
`__init__.py`, `api.py`, `bundle.py`, `devices.py`, `diagnostics.py`,
`manifest.json`, `README.md`. The other **28 existing files** retain their hashes,
including the fixed calendar implementation. All **35 resulting files** match
expected source hashes.

Verified pre-deployment backup:
`/config/backups/schulmanager_online/maintenance-20261023T085956+0200/`.
This contains five original files, before/after hashes and private comparison
snapshots. The two new helper files did not exist before deployment. No account,
student or calendar content from those snapshots was copied into this repository.

Installation used staged checksums and atomic per-file replacements with rollback
on installation failure. `ha core check` passed. One Core restart was requested
at **09:01:02 Europe/Berlin**, completed successfully, and HA reported RUNNING with
the integration loaded. A manual refresh returned HTTP 200. A subsequent entry
reload returned HTTP 200 and `require_restart: false`; the same acceptance checks
passed again after reload and registry persistence.

| Live check | Result |
| --- | --- |
| Entry IDs | Same one entry |
| Device IDs, identifiers, parent links and user metadata | Same two devices |
| Entity IDs, unique IDs, device links and user metadata | Same 21 entities |
| Entity availability | 21 states, zero unavailable |
| Sensor freshness | `data_status: loaded` |
| Calendars, fixed interval 22 October–6 November | Counts 0, 1 and 37; every full-event fingerprint unchanged |
| Bundle discovery source | `detected` |
| Bundle version / last successful API version | Both `e3cf8c0506` |
| New integration warnings/errors | Zero through 09:04:15 Europe/Berlin |
| New registry deprecations / discovery failures | Zero |

The standard HA loader advisory about using a custom integration appeared once;
this is distinct from a Schulmanager runtime warning. Historical log entries were
excluded using the activation timestamp. This is a restart/refresh/reload
observation window, not long-term monitoring. There were no disabled entities in
this live installation; preservation of disabled/ambiguous records and the
multiple-entry collision cases is covered by isolated registry regressions.
Authentication failures, outages and retries were injected only in offline tests.
AG/null-subject behavior retains the existing offline calendar coverage; no new
live AG-specific acceptance is claimed.

GitHub checks for the implementation commit:

- [Offline regressions passed](https://github.com/tkarle/schulmanager-online-hass/actions/runs/39914684376).
- [hassfest passed](https://github.com/tkarle/schulmanager-online-hass/actions/runs/39914684387).
- [HACS validation](https://github.com/tkarle/schulmanager-online-hass/actions/runs/39914684482)
  passes integration manifest and `hacs.json`, but its aggregate result still fails
  on the same pre-existing repository metadata as 1.3.0: issues disabled, no valid
  topics and license detection `NOASSERTION`. Repository settings and license text
  were not changed. This limitation does not affect the verified direct deployment.

### Rollback

After checking for intervening edits, restore the five originals from `files/` in
that backup, remove only the newly added `bundle.py` and `devices.py`, verify the
saved baseline hashes, run `ha core check` and restart Core once. The backup restores
the actual prior 1.2.2 installation, including its calendar fix; do not restore an
older calendar file or a whole-system backup.
