"""Lightweight repo-level sanity checks (no Home Assistant runtime required)."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMPONENT = ROOT / "custom_components" / "wildfire_monitor"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_manifest_is_well_formed() -> None:
    manifest = _load(COMPONENT / "manifest.json")
    assert manifest["domain"] == "wildfire_monitor"
    assert manifest["config_flow"] is True
    assert manifest["version"]


def test_manifest_version_matches_release_manifest() -> None:
    manifest = _load(COMPONENT / "manifest.json")
    release_manifest = _load(ROOT / ".release-please-manifest.json")
    assert manifest["version"] == release_manifest["."]


def test_strings_and_translations_match() -> None:
    strings = _load(COMPONENT / "strings.json")
    english = _load(COMPONENT / "translations" / "en.json")
    assert strings == english


def _png_size(path: Path) -> tuple[int, int]:
    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n", f"{path.name} is not a PNG"
    return int.from_bytes(header[16:20], "big"), int.from_bytes(header[20:24], "big")


def test_brand_icons_present() -> None:
    # HACS's `brands` check looks for exactly this file before falling back to
    # the home-assistant/brands repository, which this integration is not in.
    assert _png_size(COMPONENT / "brand" / "icon.png") == (256, 256)
    assert _png_size(COMPONENT / "brand" / "icon@2x.png") == (512, 512)


def _version(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def test_hacs_minimum_covers_the_platform_api() -> None:
    # Every platform imports AddConfigEntryEntitiesCallback, which first
    # shipped in Home Assistant 2025.3; an older install would fail at import.
    uses_new_callback = any(
        "AddConfigEntryEntitiesCallback" in path.read_text(encoding="utf-8") for path in COMPONENT.glob("*.py")
    )
    if uses_new_callback:
        assert _version(_load(ROOT / "hacs.json")["homeassistant"]) >= (2025, 3, 0)
