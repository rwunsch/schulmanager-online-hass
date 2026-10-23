"""Bounded discovery from the public web app, never from arbitrary asset hashes."""
from __future__ import annotations

import asyncio
from collections import deque
from html.parser import HTMLParser
import re
from urllib.parse import urldefrag, urljoin, urlsplit

MAX_RESOURCES = 96
MAX_DEPTH = 2
MAX_BYTES = 4 * 1024 * 1024
RESOURCE_TIMEOUT = 5
DISCOVERY_TIMEOUT = 30


class BundleDetectionError(Exception):
    """Public-page, resource-fetch or semantic version-discovery failure."""


class AppPage(HTMLParser):
    """Keep document order, script entrypoints, module preloads and the first base."""

    def __init__(self):
        super().__init__()
        self.base = None
        self.scripts = []
        self.preloads = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "base" and self.base is None:
            self.base = attrs.get("href")
        if tag == "script" and attrs.get("src"):
            self.scripts.append(attrs["src"])
        if tag == "link" and attrs.get("rel") == "modulepreload" and attrs.get("href"):
            self.preloads.append(attrs["href"])


def resource_url(base: str, reference: str) -> str | None:
    """Resolve against the actual document/resource URL and drop fragments."""
    result = urldefrag(urljoin(base, reference))[0]
    parts = urlsplit(result)
    if parts.scheme not in ("https", "http") or not parts.hostname or parts.username or parts.password:
        return None
    return result


def imports(source: str) -> list[str]:
    """Literal static/dynamic ES imports only; never evaluate JavaScript."""
    pattern = r'''(?:\bfrom\s*|\bimport\s*(?:\(\s*)?)["']([^"']+\.js(?:\?[^"']*)?)["']'''
    return list(dict.fromkeys(re.findall(pattern, source)))


def version_in_source(source: str) -> str | None:
    """Require an explicit bundleVersion literal or unique same-file binding.

    Current production uses `x="..."` and `{bundleVersion:x,requests:e}` in
    the same imported module. Filename hashes, nearby fetch/post strings and
    unresolvable/cross-module variables are deliberately insufficient evidence.
    """
    prop = r'''(?<![\w$])["']?bundleVersion["']?\s*[:=]\s*'''
    literal = r'''["']([a-fA-F0-9]{8,64})["']'''
    candidates = set(re.findall(prop + literal, source))
    for binding in re.findall(prop + r'([A-Za-z_$][\w$]*)(?=\s*[,;}])', source):
        assignment = r'(?<![\w$.])' + re.escape(binding) + r'\s*=(?!=)\s*'
        # Multiple writes (including nonliteral writes) make the binding ambiguous.
        if len(re.findall(assignment, source)) == 1:
            candidates.update(re.findall(assignment + literal, source))
    return next(iter(candidates)) if len(candidates) == 1 else None


async def fetch_source(session, url: str, stage: str) -> tuple[str, str]:
    """Read a bounded body with a per-resource timeout; redact server responses."""
    try:
        async with session.get(url, timeout=RESOURCE_TIMEOUT) as response:
            if response.status != 200:
                raise BundleDetectionError(f"{stage}: HTTP {response.status}")
            body = bytearray()
            while chunk := await response.content.read(65536):
                body.extend(chunk)
                if len(body) > MAX_BYTES:
                    raise BundleDetectionError(f"{stage}: resource exceeds size limit")
            return body.decode("utf-8", errors="replace"), str(response.url)
    except BundleDetectionError:
        raise
    except Exception as err:
        # Do not log URL query strings, cookies or response bodies from exceptions.
        raise BundleDetectionError(f"{stage}: {type(err).__name__}") from err


async def detect_bundle_version(session, entry_url: str) -> str:
    """Return a semantically identified version or raise; no fallback/cache here.

    Follow at most 96 JS resources, two import levels and 30 seconds in total.
    Initial scripts may be on CDNs; imports stay on their parent resource origin.
    Redirect destinations and HTML base href control relative URL resolution.
    """
    try:
        async with asyncio.timeout(DISCOVERY_TIMEOUT):
            html, document_url = await fetch_source(session, entry_url, "HTML fetch")
            page = AppPage()
            page.feed(html)
            base = resource_url(document_url, page.base or "")
            if base is None:
                raise BundleDetectionError("resource resolution: invalid document base")
            # Main entrypoints precede polyfills; everything else keeps source order.
            scripts = sorted(page.scripts, key=lambda ref: "main" not in urlsplit(ref).path)
            queue = deque((resource_url(base, ref), 0) for ref in scripts + page.preloads)
            seen = set()
            failures = []
            while queue and len(seen) < MAX_RESOURCES:
                url, depth = queue.popleft()
                if not url or url in seen:
                    continue
                seen.add(url)
                try:
                    source, final_url = await fetch_source(session, url, "JS fetch")
                except BundleDetectionError as err:
                    failures.append(str(err))
                    continue
                seen.add(final_url)
                if version := version_in_source(source):
                    return version
                if depth < MAX_DEPTH:
                    for ref in imports(source):
                        target = resource_url(final_url, ref)
                        if target and urlsplit(target).netloc == urlsplit(final_url).netloc:
                            queue.append((target, depth + 1))
            detail = f"; {failures[-1]}" if failures else ""
            raise BundleDetectionError(
                f"value detection: no unambiguous bundleVersion in {len(seen)} resources{detail}"
            )
    except TimeoutError as err:
        raise BundleDetectionError("discovery timeout: total time limit reached") from err
