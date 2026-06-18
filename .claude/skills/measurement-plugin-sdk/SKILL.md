---
name: measurement-plugin-sdk
description: Conventions for writing measurement.py with the NI Measurement Plug-In SDK (ni_measurement_plugin_sdk). Use when creating or editing a measurement.py — the @register_measurement / @configuration / @output decorators, pin reservation and session init, streaming with yield, enum/IOResource parameters, and the framework-separation pattern that keeps logic testable. Pairs with the find-meas-example skill (which finds the right DataType/UI control).
---

# measurement-plugin-sdk

How to structure `measurement.py`. This skill carries the *conventions*; the **verified
examples are the source of truth for exact code** — use the `find-meas-example` skill and
copy from the real sample. Do not author decorator stacks or session blocks from memory.

## When to use

Creating or editing `measurement.py`, or wiring up configuration/output parameters, pins,
sessions, or streaming.

## Core conventions (confirmed across the samples under `src/examples/meas-plugin/`)

1. **Decorator stack** on `measure()` — order matters; copy the shape from a sample:
   ```python
   @measurement_service.register_measurement
   @measurement_service.configuration("pin_names", nims.DataType.IOResource, "Pin1",
       instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER)
   @measurement_service.configuration("voltage_level", nims.DataType.Double, 6.0)
   @measurement_service.output("voltage_measurements", nims.DataType.DoubleArray1D)
   def measure(pin_names, voltage_level): ...
   ```
   - The DisplayName string in each decorator must match the `.measui` `Channel` binding
     exactly (see `docs/measui-reference.md` §3).
   - For a DataType you have not used yet, run
     `.claude/skills/find-meas-example/find_example.sh <DataType>` first.

2. **Enum / IOResource parameters:** `DataType.Enum` takes `enum_type=<IntEnum>`;
   `DataType.IOResource` takes `instrument_type=...`. See examples via the find-meas-example
   skill.

3. **Pins and sessions — never hardcode resource names.** Reserve by pin name and let the
   session-management service resolve hardware from the pin map:
   ```python
   with measurement_service.context.reserve_sessions(pin_names) as reservation:
       with reservation.initialize_nidcpower_sessions() as session_infos:
           ...
   ```

4. **Streaming:** `yield` partial results to update the UI in real time; the function is a
   generator when it streams. Yield a complete tuple of all outputs each time.

5. **Framework-separation for testability (required by @docs/test-design.md):** `measure()`
   is a thin orchestrator. Put logic in:
   - pure calculation functions (no instrument/framework calls) → Layer 1 unit tests,
   - mode/handler functions taking session objects → Layer 2 tests with the simulated driver,
   - `measure()` only reserves sessions and dispatches.
   Use the exact function names listed in the project's `docs/specs/<name>_test_cases.md`.

6. **Simulation must work without hardware** — honor the simulation env vars from @CLAUDE.md
   (a `.env` in the plug-in directory). All code must run with simulated instruments.

## Reference

- Exact code patterns: the `find-meas-example` skill + the samples it points to.
- Testability decomposition and the four test layers: @docs/test-design.md.
- Project rules (no hardcoded resources, simulation support, English only): @CLAUDE.md.
