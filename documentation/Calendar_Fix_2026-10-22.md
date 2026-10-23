# Calendar regression fix — 1.2.2

## Scope and source comparison

Fix commit: `4a83099bb4eaef43da977de0b759a6c6709240ac`, based on
`64fef58` (`v1.2.1`), on the existing `fix/stable-sensor-defaults` release branch.
The verified origin is `git@github.com:tkarle/schulmanager-online-hass.git`.
All 33 deployed integration files matched the repository before modification.
The existing branch includes the previous integration extensions; it was not
replaced with the older `main` branch.

The subject now falls back from null/empty `subject` to `subject_name`, then
`Lesson`. An empty class-hour number is initialized explicitly and omitted from
the description. Unnumbered lessons still use their supplied start/end times.
No changes were made to substitutions, cancellations, highlighting, grouping,
the bundle-version fallback, or device-registry calls.

## Regression checks

`python3 -m unittest discover -s tests -v`: **17 tests pass** on Python 3.14.6.
The ten new calendar tests import the real calendar module and helpers with a
minimal HA boundary stub. They cover null/empty/missing subjects with/without
rooms, subject-name/default fallback, missing/null/empty class-hour numbers,
exact AG times, API class-hour times, substitutions and cancellations with
highlighting on/off, hidden cancellations, replacement de-duplication in both
input orders, separate unnumbered lessons, free hours, and date filtering.
Every calendar test also rejects unexpected warning/error logs.

Before the fix, the new suite reproduced both the `NoneType += str` failure and
the uninitialized `class_hour_number` failure. These are offline unit tests,
not a complete HA integration test suite. The existing coordinator tests needed
their HA stub extended for the already-used `homeassistant.util.dt.now()` import;
no coordinator production code was changed.

`python3 -m compileall -q custom_components/schulmanager_online tests` and
`git diff --check` passed. The new GitHub Actions workflow runs the synthetic
regressions on pushes and pull requests.

GitHub checks for the fix commit:

- [Offline regressions: passed](https://github.com/tkarle/schulmanager-online-hass/actions/runs/39806785112).
- [hassfest: failed](https://github.com/tkarle/schulmanager-online-hass/actions/runs/39806785896)
  on pre-existing manifest content: unsupported `homeassistant` field and
  explicitly listed HA dependency `aiohttp>=3.8.0`. Both values are present in
  `v1.2.1`; this fix only changes the manifest version.
- [HACS: failed](https://github.com/tkarle/schulmanager-online-hass/actions/runs/39806785113)
  on repository metadata: missing valid topics, issues disabled, license
  detection `NOASSERTION`. Repository settings and license were left unchanged.

## Deployment

Target: Home Assistant Core **2026.10.2**,
`/config/custom_components/schulmanager_online`.
The historical `deploy.sh` still contains an obsolete source path and target.
The deployment therefore used the established SSH file-install/Core-restart
procedure with the actual configured host, limited to the two changed files.
It did not run the obsolete script's directory deletion/full replacement.

Before replacement, copies of **calendar.py** and **manifest.json** were created
and verified against the pre-deployment SHA-256 hashes in:

`/config/backups/schulmanager_online/calendar-fix-20261022T173831+0200/`

Installation completed at **17:38:31 Europe/Berlin**, using staged files and
atomic per-file replacement with rollback on installation failure. All **31
other integration files** retained their original checksums. `ha core check`
completed successfully. A single `ha core restart` was used to activate the new
Python module; reloading a config entry alone does not re-import its module.

Deployed SHA-256:

| File | SHA-256 |
| --- | --- |
| calendar.py | `0626e928553242e449cf54302a579f55d79280a2a2deb23ef5d90601f0419735` |
| manifest.json | `4a66fc17c9c6dd2173092cea07f649838d8aba96d323fe967722c9a4bd5d9e03` |

## Live acceptance

The Core restart completed successfully. The REST API confirmed HA **RUNNING**,
the integration entry **loaded**, and sensor data status **loaded**. A targeted
`schulmanager_online.refresh` fetched current data before querying the calendar.

The same date-range request now returns **37 events**, compared with **35**
before deployment. Both affected event fingerprints match returned calendar
events, including their title, date, start time and end time. A second request
also returns **37 events**. Since deployment, timestamp-filtered Core logs show
**zero** new lesson-creation warnings (including both reported errors) and
**zero** integration error lines.

No live unnumbered AG was identified in the sensor snapshot, so AG behavior is
verified by the synthetic regressions preserving the exact 14:17–15:42 interval,
not claimed as an observed live AG result. The observation window covers the
restart, manual refresh and repeated calendar retrieval; it is not a long-term
monitoring result.

The baseline calendar request returned **35 events** over the same fixed date
range used for the subsequent check. The available pre-deployment log contained
**35** lesson-creation warnings, all matching the null-subject failure, and no
class-hour-variable warnings. Two distinct affected candidates were identified
in sensor data and retained only as event fingerprints for comparison on the
HA host. No private lesson or student data was added to Git or test fixtures.

## Rollback

Restore both backed-up files from the directory above to the live integration
directory and restart HA Core once. This restores version 1.2.1 and its original
calendar implementation without changing the other integration files.
