"""Verify the catalog against each plugin's pinned release.

Structural checks run offline. With --online (the default in CI) every entry's
pinned ref is fetched from its own repository and the catalog's advertised
metadata is compared against that release's plugin.json, so a catalog can never
advertise a version, licence or description the release does not actually carry.

Exit code 0 means every assertion passed. Any failure prints one line per
problem and exits 1.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
# Release tags name versions; a separate full commit SHA supplies the immutable pin.
RELEASE_TAG = re.compile(r"v(\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)")
# Names Claude Code reserves, plus package-manager names it refuses.
RESERVED = {
    "claude-code-marketplace", "claude-code-plugins", "claude-plugins-official",
    "claude-plugins-community", "claude-community", "anthropic-marketplace",
    "anthropic-plugins", "agent-skills", "anthropic-agent-skills",
    "knowledge-work-plugins", "life-sciences", "claude-for-legal",
    "claude-for-financial-services", "financial-services-plugins",
    "first-party-plugins", "claude-tag-plugins", "healthcare",
    "npm", "pip", "uv", "cargo", "github", "gh",
}
# Fields the catalog advertises that must match the release's own manifest.
MIRRORED = ("displayName", "description", "homepage", "repository", "license")
GIT_SOURCES = {"git-subdir", "github", "url"}


def strict_load(text: str) -> Any:
    """Reject duplicate keys rather than silently keeping the last one."""
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        seen: dict[str, Any] = {}
        for key, value in pairs:
            if key in seen:
                raise ValueError(f"duplicate JSON key: {key}")
            seen[key] = value
        return seen
    return json.loads(text, object_pairs_hook=no_duplicates)


def repo_url(source: dict[str, Any]) -> str:
    if source.get("source") == "github":
        return "https://github.com/" + str(source.get("repo", "")) + ".git"
    return str(source.get("url", ""))


def fetch_manifest(source: dict[str, Any], timeout: int) -> dict[str, Any]:
    """Read one release's plugin.json without checking out or running anything."""
    url = repo_url(source)
    ref = str(source.get("ref", ""))
    subdir = str(source.get("path", "")).strip("/")
    manifest_path = f"{subdir}/.claude-plugin/plugin.json" if subdir else ".claude-plugin/plugin.json"
    with tempfile.TemporaryDirectory() as tmp:
        def git(*args: str) -> bytes:
            return subprocess.run(
                ["git", "-C", tmp, *args],
                check=True, capture_output=True, timeout=timeout,
            ).stdout
        git("init", "-q")
        git("remote", "add", "origin", url)
        # A tag ref is fetched by its full refs/tags/ name so a same-named
        # branch on the remote can never be substituted for it.
        git("fetch", "-q", "--depth", "1", "origin", f"refs/tags/{ref}:refs/tags/{ref}")
        tagged = git("rev-parse", f"refs/tags/{ref}^{{commit}}").decode().strip()
        sha = source["sha"]
        if tagged != sha:
            raise ValueError(f"release tag {ref} resolves to {tagged}, not catalog SHA {sha}")
        # Read the effective installed revision, not just a similarly named tag.
        return strict_load(git("show", f"{sha}:{manifest_path}").decode("utf-8"))


def check_entry(entry: dict[str, Any], errors: list[str], online: bool, timeout: int) -> None:
    name = entry.get("name", "<unnamed>")

    def bad(message: str) -> None:
        errors.append(f"{name}: {message}")

    if not isinstance(name, str) or not KEBAB.fullmatch(name):
        bad("plugin name must be kebab-case")
    if "version" in entry:
        bad("entry must not set 'version'; the release's plugin.json is the authority")

    source = entry.get("source")
    if not isinstance(source, dict):
        bad("source must be a pinned object, not a relative path in a published catalog")
        return
    kind = source.get("source")
    if kind not in GIT_SOURCES:
        bad(f"unsupported source type {kind!r}")
        return

    ref = str(source.get("ref", ""))
    tag = RELEASE_TAG.fullmatch(ref)
    if not tag:
        bad(f"ref {ref!r} is not a release tag (expected vMAJOR.MINOR.PATCH)")
    valid_sha = re.fullmatch(r"[0-9a-f]{40}", str(source.get("sha", "")))
    if not valid_sha:
        bad("sha is required and must be a full 40-character lowercase commit id")

    url = repo_url(source)
    if not url.startswith("https://"):
        bad(f"source url must be https, got {url!r}")
    subdir = str(source.get("path", ""))
    if subdir.startswith("/") or ".." in Path(subdir).parts:
        bad(f"source path {subdir!r} must be relative and contained")

    for field in MIRRORED:
        if not entry.get(field):
            bad(f"entry is missing {field}")
    if not entry.get("tags") and not entry.get("keywords"):
        bad("entry needs tags or keywords")
    if entry.get("defaultEnabled") not in (None, False, True):
        bad("defaultEnabled must be a boolean")

    if not online or not tag or not valid_sha:
        return

    try:
        manifest = fetch_manifest(source, timeout)
    except subprocess.CalledProcessError as error:
        detail = error.stderr.decode("utf-8", "replace").strip().splitlines()[-1:] or [""]
        bad(f"could not read plugin.json at {ref}: {detail[0]}")
        return
    except (subprocess.TimeoutExpired, ValueError, UnicodeDecodeError) as error:
        bad(f"could not read plugin.json at {ref}: {error}")
        return

    if manifest.get("name") != name:
        bad(f"release declares name {manifest.get('name')!r}, catalog says {name!r}")
    # The check that matters most: a catalog pointing at the wrong release.
    if manifest.get("version") != tag.group(1):
        bad(f"ref {ref} does not match the release's version {manifest.get('version')!r}")
    for field in MIRRORED:
        if entry.get(field) != manifest.get(field):
            bad(f"{field} differs: catalog {entry.get(field)!r} vs release {manifest.get(field)!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=Path(".claude-plugin/marketplace.json"))
    parser.add_argument("--offline", action="store_true",
                        help="skip fetching each pinned release (structure only)")
    parser.add_argument("--timeout", type=int, default=60)
    args = parser.parse_args()

    errors: list[str] = []
    try:
        catalog = strict_load(args.catalog.read_text(encoding="utf-8"))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"catalog could not be read: {error}", file=sys.stderr)
        return 1

    name = catalog.get("name")
    if not isinstance(name, str) or not KEBAB.fullmatch(name):
        errors.append("catalog name must be kebab-case")
    elif name in RESERVED:
        errors.append(f"catalog name {name!r} is reserved")
    owner = catalog.get("owner")
    if not isinstance(owner, dict) or not owner.get("name"):
        errors.append("catalog needs an owner with a name")

    plugins = catalog.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        errors.append("catalog needs a non-empty plugins list")
        plugins = []
    seen: set[str] = set()
    for entry in plugins:
        if not isinstance(entry, dict):
            errors.append("each plugin entry must be an object")
            continue
        if entry.get("name") in seen:
            errors.append(f"duplicate plugin entry {entry.get('name')!r}")
        seen.add(entry.get("name"))
        check_entry(entry, errors, not args.offline, args.timeout)

    if errors:
        for error in errors:
            print(f"FAIL {error}", file=sys.stderr)
        return 1
    scope = "structure" if args.offline else "structure and pinned releases"
    print(f"PASS {name}: {len(plugins)} plugin(s) verified ({scope})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
