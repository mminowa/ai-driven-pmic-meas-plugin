---
description: Phase 2 (Test Definition) — derive test cases from the spec into docs/specs/<name>_test_cases.md. No production code.
argument-hint: <short_name>  e.g. buck_ripple
---

You are running **Phase 2 — Test Definition** of the Specification-Driven Development process
in @CLAUDE.md. The plug-in short name is: **$1**

## Hard rule

Tests are defined **before** production code. Do not write `measurement.py` or any
implementation. Phase 2 produces the test-cases document only.

## Reference (mirror their structure)

- Testing strategy and the four layers: @docs/test-design.md
- Test-cases template: @docs/specs/pmic_efficiency_test_cases.md
- The spec to verify: `docs/specs/$1.md` (read it first; if missing, tell the user to run
  `/spec $1` first and stop)

## Steps

1. **Read `docs/specs/$1.md`** in full. The test cases must cover its inputs, outputs, modes,
   and edge cases — nothing outside the spec.

2. **Write `docs/specs/$1_test_cases.md`** mirroring the template, including:
   - Project-Specific Configuration:
     - Plug-in file prefix.
     - Layer 2 simulation options (`simulate=True` + `driver_setup` per the driver in the spec).
     - Orchestration Functions table: pure calculation functions (Layer 1 unit-testable),
       mode handler functions (Layer 2 with the simulated driver), and a thin `measure()` that
       only dispatches — each with its signature and testability (per @docs/test-design.md).
   - **Layer 1** unit cases: concrete input → expected output tables (include boundary/NaN/guard cases).
   - **Layer 2** integration cases: output shapes, state transitions, cancellation, streaming yields.
   - **Layer 3** smoke cases: required-files list only (3-3). Cases 3-1 and 3-2 are generic and
     fully defined in @docs/test-design.md — do not repeat them here.
   - **Layer 4** manual end-to-end checklist (per mode).

3. **Confirm with the user** and state that Phase 3 is next, starting with
   `/scaffold $1 <MeasurementName>` (then `/implement $1` → `/gen-measui $1` →
   `/refine-measui $1`).

Keep all documentation in **English**.
