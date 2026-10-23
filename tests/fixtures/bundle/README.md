# Public bundle-discovery fixture

Retrieved from the unauthenticated public application on 22 October 2026 and
rechecked on 23 October. No account, cookie, authentication response or school
or student data was used. These are small source excerpts, not executable copies
of the application. Unrelated content is omitted.

- HTML: https://login.schulmanager-online.de/ — base href, module preloads and
  script entrypoints retained, including `static/main-3NS7PKZO.js`.
- Main: https://login.schulmanager-online.de/static/main-3NS7PKZO.js — the
  actual static import of `chunk-VHWXMUR6.js` retained.
- API module: https://login.schulmanager-online.de/static/chunk-VHWXMUR6.js —
  the `x="e3cf8c0506"` binding and `bundleVersion:x` request property retained.

Version 1.3.0 only scans HTML script references and does not follow this import;
on this fixture it returns its historical `3505280ee7` fallback. The new detector
returns the binding used in the API payload. The production search is verified
separately against the complete live public sources; asset names are not coded
into the detector.
