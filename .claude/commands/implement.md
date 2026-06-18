---
description: Phase 3 (Implementation) — scaffold the plug-in, write measurement.py + tests to satisfy the spec and test cases, then verify.
argument-hint: <short_name> <MeasurementName>  e.g. buck_ripple BuckRipple
---

You are running **Phase 3 — Implementation** of the Specification-Driven Development process
in @CLAUDE.md. Short name: **$1**. Measurement (display) name: **$2**.

## Hard rule

Do not implement anything not covered by `docs/specs/$1.md` and `docs/specs/$1_test_cases.md`.
Read both first; if either is missing, tell the user to run `/spec $1` and/or
`/test-cases $1` first and stop.

## Reference

- Step-by-step setup procedure (Poetry, generator, file moves): the **Plug-In Technical Setup**
  section of @CLAUDE.md — follow it exactly.
- Reference example to template from: see **Project-Specific Configuration** in @CLAUDE.md.
- `.measui` authoring: use the **find-meas-example** skill for the correct control/XML per data
  type, follow @docs/update-measui.md, avoid the failures in @docs/measui-gotchas.md, and lint
  with `python scripts/validate_measui.py <file.measui>`.

## Steps

1. **Scaffold** following @CLAUDE.md Plug-In Technical Setup: create `src/$1/`, write
   `pyproject.toml` (with `ni_measurement_plugin_sdk` + the driver(s) from the spec),
   `poetry.toml`, `install.bat`, `.serviceignore`; `poetry install`; run
   `poetry run ni-measurement-plugin-generator $2`; move the generated files up and remove the
   subdirectory. Create the `.env` file with the simulation env vars from @CLAUDE.md.

2. **Implement `measurement.py`** to satisfy the spec, using the exact function decomposition
   from `docs/specs/$1_test_cases.md` (pure calc functions, mode handlers, thin `measure()`
   that dispatches). Resource names come from the pin map / configuration — never hardcode
   them. Define the `.pinmap` per the spec.

3. **Write the tests** under `src/$1/tests/` matching the four layers in @docs/test-design.md:
   `test_calculations.py` (Layer 1), `test_measurement.py` (Layer 2, simulated driver),
   `test_smoke.py` (Layer 3). Implement every Layer 1–3 case from the test-cases document.

4. **Author the `.measui`** per `docs/specs/$1_ui.md`: for each control, run
   `.claude/skills/find-meas-example/find_example.sh <DataType-or-control>` and copy from the
   verified sample it points to; then lint with `python scripts/validate_measui.py`.

5. **Verify.** Run `poetry run pytest` for Layers 1–3 and report results honestly (show
   failures with their output). Note that Layer 4 and live `.measui` loading require Windows +
   the running service, so they cannot be verified here.

Keep all code, comments, and commit messages in **English**.
