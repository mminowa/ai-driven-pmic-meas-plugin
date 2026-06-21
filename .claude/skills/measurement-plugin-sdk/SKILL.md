---
name: measurement-plugin-sdk
description: SDK-specific patterns for measurement.py that are hard to find in the reference examples. Covers DataType selection, streaming with yield (when the spec requires real-time output), and simulation via the framework. Use alongside the Driver-specific reference examples in CLAUDE.md.
---

# measurement-plugin-sdk

SDK patterns that are easy to get wrong or hard to find in the reference examples.
Read the Driver-specific reference examples in @CLAUDE.md for all other boilerplate.

## DataType reference

For the full `DataType` enum and decorator signatures, locate the SDK source files with:

```bash
python -c "
import ni_measurement_plugin_sdk_service.measurement.info as i
import ni_measurement_plugin_sdk_service.measurement.service as s
print(i.__file__)
print(s.__file__)
"
```

Then read the two files:
- `info.py` — all `DataType` enum values
- `service.py` — `configuration()` and `output()` decorator signatures

Non-obvious rules not visible from the enum alone:

- `DataType.Pin` / `DataType.PinArray1D` are **deprecated** — use `IOResource` / `IOResourceArray1D` instead.
- `DoubleXYData`, `Double2DArray`, `String2DArray`, `DoubleXYDataArray1D` are **output only** — passing them to `configuration()` raises `ValueError`.
- `IOResource` / `IOResourceArray1D` should include `instrument_type=` (a constant from `ni_measurement_plugin_sdk_service.session_management`, e.g. `INSTRUMENT_TYPE_NI_DCPOWER`). Omitting it does not raise an error but disables instrument-type filtering in the pin map.
- `Enum` / `EnumArray1D` require `enum_type=` — a Python `enum.Enum` subclass (or protobuf enum) where at least one member has value `0`. Omitting `enum_type` raises `ValueError`.

## Streaming with `yield` (only when the spec requires real-time output)

Most measurements use `return`. Use `yield` only when the spec explicitly requires
real-time streaming of partial results to the UI during the measurement loop.

When streaming is required:
- `measure()` becomes a generator — use `yield`, never `return`.
- Yield a complete tuple of **all** outputs each time (partial arrays mid-loop, then
  completed arrays at the end).
- If a mode handler is also a generator, delegate with `yield from _run_handler(...)`.

The only reference example showing this pattern is
`src/examples/meas-plugin/game_of_life/measurement.py`.

## Simulation via the framework — not via `nidcpower.Session(options=…)`

The standalone driver examples pass `options={'simulate': True, ...}` directly to
`nidcpower.Session`. Do **not** do this in `measurement.py`. The framework injects simulation
settings from the `.env` file automatically when `initialize_nidcpower_sessions()` is called.
`measurement.py` requires no change to run in simulation vs. real hardware.

**Layer 2 integration tests are exempt from this rule.** Integration tests call helper
functions directly with sessions they create themselves, bypassing the framework. Passing
`options={'simulate': True, ...}` directly to the driver session constructor is correct
and expected in test code.
