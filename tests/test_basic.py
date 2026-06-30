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
