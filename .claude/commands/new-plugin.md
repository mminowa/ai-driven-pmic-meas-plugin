---
description: Reuse this repo as a template for a NEW Measurement Plug-In — update only the Project-Specific Configuration sections, then hand off to Phase 1 (/spec).
argument-hint: <short_name>  e.g. buck_ripple
---

You are repurposing this template repository for a **new** Measurement Plug-In. The plug-in
short name is: **$1**. If `$1` is empty, ask the user for it first.

## Scope — what this command does and does not touch

This template is designed so that reuse means **editing only the "Project-Specific
Configuration" sections**. Everything else in @CLAUDE.md and @docs/update-measui.md applies to
any plug-in built with this framework and must stay unchanged.

- **Edit only**: the `## Project-Specific Configuration` section of @CLAUDE.md and the
  "Project-Specific Configuration" table of @docs/update-measui.md.
- **Do NOT**: write specs, source code, tests, or `.measui` here — those come in later phases.
- **Do NOT**: alter the generic procedure text, constraints, or directory rules.

## Steps

1. **Gather the project facts** with the AskUserQuestion tool (do not guess hardware,
   drivers, or model numbers):
   - What the plug-in measures (one sentence).
   - Plug-in directory: `src/$1/`.
   - Hardware roles → instruments → driver package(s) (e.g. `nidcpower`, `nidaqmx`).
   - Simulation environment variables (driver, board type, model) for the `.env` file.
   - Measurement display name (e.g. `BuckRipple`) and the generated `.measui` filename.

2. **Update @CLAUDE.md** — replace the contents of the `## Project-Specific Configuration`
   section (the part the template marks as "update only this section") with the gathered
   values: what it measures, plug-in directory, the hardware-targets table, simulation env
   vars, and the driver-specific reference example paths. Leave the rest of the file intact.

3. **Update @docs/update-measui.md** — set the "Project-Specific Configuration" table:
   plug-in directory, measurement service name, generated `.measui` filename, and the UI
   spec file path (`docs/specs/$1_ui.md`).

4. **Confirm** the two edited sections back to the user and state the next step:
   `/spec $1` (Phase 1 — Specification). Note that no spec or source has been created yet.

Keep all documentation in **English**.
