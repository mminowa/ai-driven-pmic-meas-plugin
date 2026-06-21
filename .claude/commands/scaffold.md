---
description: Phase 3 step 1 of 4 — scaffold the plug-in project (Poetry, generator, file moves). No measurement logic, tests, or UI.
argument-hint: <short_name> <MeasurementName>  e.g. buck_ripple BuckRipple
---

You are running the **scaffold** step of Phase 3 (Implementation) of the Specification-Driven
Development process in @CLAUDE.md. Short name: **$1**. Measurement (display) name: **$2**.

Phase 3 is split into four commands run in order:
`/scaffold` → `/implement` → `/gen-measui` → `/refine-measui`. Do only the scaffold here; stop
before writing any measurement logic, tests, or `.measui`.

## Hard rule

Do not start unless the specification exists. Read `docs/specs/$1.md` and
`docs/specs/$1_test_cases.md` first; if either is missing, tell the user to run `/spec $1`
and/or `/test-cases $1` first and stop. You only need the spec here to pick the driver
dependencies — do not implement anything it describes.

## Reference

- Step-by-step setup procedure: the **Plug-In Technical Setup** section of @CLAUDE.md,
  **Steps 0–4** — follow it exactly.
- Reference example to template from: see **Project-Specific Configuration** in @CLAUDE.md.

## Steps

Follow @CLAUDE.md Plug-In Technical Setup, **Steps 0–4**:

0. **Install Poetry** and add it to PATH (skip if already available — check `poetry --version`).
1. **Create the plug-in directory and `pyproject.toml`**: create `src/$1/` and write
   `pyproject.toml` with `ni_measurement_plugin_sdk` + the driver(s) named in the spec. Use the
   reference example in `src/examples/meas-plugin/` as a template.
2. **Add Poetry-related files**: write `poetry.toml`, `install.bat`, and `.serviceignore` in
   `src/$1/` (contents per @CLAUDE.md Step 2).
3. **Install dependencies**: run `poetry install` inside `src/$1/`.
4. **Generate the plug-in scaffold**: run `poetry run ni-measurement-plugin-generator $2`, then
   move the generated files up into `src/$1/` and remove the now-empty `$2/` subdirectory.

Then create the `.env` file with the simulation env vars from @CLAUDE.md (the **Simulation**
subsection of Plug-In Technical Setup).

Leave the generated `measurement.py` and `.measui` exactly as the generator produced them — do
not edit them here.

## Finish

Report what was created and confirm `poetry install` succeeded. Tell the user the next step is
`/implement $1` (write `measurement.py` + unit tests).

Keep all files, comments, and commit messages in **English**.
