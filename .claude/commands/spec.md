---
description: Phase 1 (Specification) — interview and write a formal spec under docs/specs/ for a new Measurement Plug-In. No source code.
argument-hint: <short_name>  e.g. buck_ripple
---

You are running **Phase 1 — Specification** of the Specification-Driven Development process
defined in @CLAUDE.md. The plug-in short name is: **$1**

## Hard rule

Do **NOT** create any source files (`measurement.py`, `pyproject.toml`, `tests/`, etc.).
Phase 1 produces specification documents only. If `$1` is empty, ask the user for the
short name before continuing.

## Reference (mirror their structure — do not invent a new format)

- Measurement spec template: @docs/specs/pmic_efficiency.md
- UI spec template: @docs/specs/pmic_efficiency_ui.md
- Project rules and constraints: @CLAUDE.md

## Steps

1. **Gather the facts.** Determine each of the following. For anything not already stated by
   the user or derivable from @CLAUDE.md, ask with the AskUserQuestion tool (batch related
   questions). Do not guess instruments, drivers, or units.
   - What the plug-in measures (purpose) and any operating modes.
   - Hardware roles → instruments → drivers, and the pins (pin map).
   - Inputs (configuration parameters): name, type, default, unit, description.
   - Outputs: name, type, unit, shape, description.
   - Sweep / test flow structure (loops, yields, setup/teardown common steps).
   - Constraints (instrument limits, safe states, simulation env vars).

2. **Write `docs/specs/$1.md`** mirroring the section layout of the measurement spec template
   (Purpose, Instrument Configuration, Pin Map, Inputs, Sweep Structure, Outputs, Test Flow,
   Constraints). Use a pin-map / configuration source for resource names — never hardcode
   resource names (see Repository Rules in @CLAUDE.md). Ensure the design is runnable with
   **simulated instruments**.

3. **Write `docs/specs/$1_ui.md`** mirroring the UI spec template (Layout panes, each control
   with its type and channel binding). For each output/input, note the intended UI control
   type, but defer exact `.measui` authoring to Phase 3.

4. **Confirm with the user.** Summarize the two files and the key decisions, and ask for
   agreement. State explicitly that no source has been written and that Phase 2
   (`/test-cases $1`) is next.

Keep all documentation in **English**.
