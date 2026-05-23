"""Layer 3 — Smoke tests: import and required file existence.

No hardware or running service required.
These tests will fail until Phase 3 creates the plug-in directory and files.

Test design ref: docs/specs/pmic_efficiency_test_cases.md — Layer 3, sections 3-1 through 3-3
"""

import json

import pytest

from conftest import PLUGIN_DIR

# ---------------------------------------------------------------------------
# 3-1. Import
# ---------------------------------------------------------------------------


def test_measurement_module_imports() -> None:
    import measurement  # noqa: F401


# ---------------------------------------------------------------------------
# 3-2. Service config is valid JSON with required fields
# ---------------------------------------------------------------------------


def test_serviceconfig_is_valid_json() -> None:
    config_path = PLUGIN_DIR / "PMICEfficiency.serviceconfig"
    assert config_path.exists(), f"serviceconfig not found: {config_path}"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    service = data["services"][0]
    assert "displayName" in service
    assert "serviceClass" in service
    assert "providedInterfaces" in service
    assert "path" in service


# ---------------------------------------------------------------------------
# 3-3. Required files exist
# ---------------------------------------------------------------------------


_REQUIRED_FILES = [
    "measurement.py",
    "_helpers.py",
    "PMICEfficiency.measui",
    "PMICEfficiency.serviceconfig",
    "PMICEfficiency.pinmap",
    "start.bat",
    "install.bat",
    ".serviceignore",
]


@pytest.mark.parametrize("filename", _REQUIRED_FILES)
def test_required_file_exists(filename: str) -> None:
    path = PLUGIN_DIR / filename
    assert path.exists(), f"Required file missing: {path}"
