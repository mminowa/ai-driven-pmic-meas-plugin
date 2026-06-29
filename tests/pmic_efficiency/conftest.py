"""Pytest configuration: add the plug-in source directory to sys.path."""

import pathlib
import sys

# Allow tests to import measurement.py from the plug-in directory.
_PLUGIN_DIR = pathlib.Path(__file__).parent.parent.parent / "src" / "pmic_efficiency"
sys.path.insert(0, str(_PLUGIN_DIR))

PLUGIN_DIR = _PLUGIN_DIR
