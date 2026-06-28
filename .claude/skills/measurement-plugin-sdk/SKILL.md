---
name: measurement-plugin-sdk
description: SDK-specific patterns for measurement.py that are hard to find in the reference examples. Covers DataType selection, streaming with yield (when the spec requires real-time output), simulation via the framework, and keeping mode handlers free of gRPC dependencies for Layer 2 testability. Use alongside the Driver-specific reference examples in CLAUDE.md.
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

## Making mode handlers testable (Layer 2)

Mode handlers (e.g. `_run_power_on`, `_run_measurement`) are called directly in Layer 2
tests without a running gRPC service. The design rule is:

> **Mode handlers must contain zero references to `measurement_service.context`.**
> All gRPC-specific logic belongs exclusively in `measure()`.

### `_wait_for_event` — cancellation-aware polling

The key line in `measure()` that makes mode handlers gRPC-free:

```python
measurement_service.context.add_cancel_callback(cancellation_event.set)
```

The gRPC framework calls this callback on **both** user cancellation and deadline
exceeded. A single `threading.Event` therefore captures all stop conditions — mode
handlers never need to touch `measurement_service.context`.

`_MeasurementCancelledError` carries the stop signal back to `measure()`:

```python
class _MeasurementCancelledError(Exception):
    """Raised when the cancellation event is set."""
```

nidcpower's `wait_for_event()` blocks and cannot be interrupted mid-call. Polling with
a 100 ms timeout bounds the cancellation response latency to at most 100 ms. Note
`continue` — it jumps back to the top of the while loop, bypassing `raise`. The
reference example uses `pass` instead, which does not change control flow, so `raise`
always executes and timeout `DriverError`s propagate instead of being suppressed and
retried:

```python
def _wait_for_event(
    channels,
    cancellation_event: threading.Event,
    event_id: nidcpower.enums.Event,
    timeout: float,
) -> None:
    user_deadline = time.time() + timeout
    while True:
        if time.time() > user_deadline:
            raise TimeoutError("User timeout expired.")
        if cancellation_event.is_set():
            raise _MeasurementCancelledError()
        try:
            channels.wait_for_event(event_id, timeout=100e-3)
            return
        except nidcpower.errors.DriverError as e:
            if e.code in _NIDCPOWER_TIMEOUT_ERROR_CODES:
                continue
            raise
```

### Mode handlers — ExitStack callbacks for cleanup

For modes that must turn outputs **off** on exit (e.g. `_run_measurement`), register
`channels.reset()` as ExitStack callbacks so cleanup runs on any exit path
(normal, cancelled, or error). Do not register reset callbacks in Power On mode
handlers — outputs must stay active after the handler returns. Exceptions propagate
out of the handler to `measure()`:

```python
def _run_measurement(..., cancellation_event: threading.Event):
    with ExitStack() as stack:
        stack.enter_context(source_ch.initiate())
        stack.enter_context(load_ch.initiate())
        stack.callback(source_ch.reset)   # registered after initiate(), so runs before abort() (LIFO)
        stack.callback(load_ch.reset)

        _wait_for_event(source_ch, cancellation_event, ..., timeout)
        _wait_for_event(load_ch, cancellation_event, ..., timeout)

        results = []
        for vin in vin_levels:
            source_ch.voltage_level = vin
            _wait_for_event(source_ch, cancellation_event, ..., timeout)
            for iout in iout_levels:
                if cancellation_event.is_set():
                    raise _MeasurementCancelledError()
                load_ch.current_level = iout
                _wait_for_event(load_ch, cancellation_event, ..., timeout)
                results.append(...)

    return results
```

For generator handlers (streaming with `yield`), the same ExitStack pattern applies,
with one critical placement rule:

> **Intermediate yields go inside the `with ExitStack()` block (outputs active).
> The final yield goes outside it, after `reset()` has already run.**

```python
def _run_measurement(..., cancellation_event: threading.Event):
    # Accumulate results across the sweep
    vin_meas_list, eff_meas_list = [], []

    with ExitStack() as stack:
        stack.enter_context(source_ch.initiate())
        stack.enter_context(load_ch.initiate())
        stack.callback(source_ch.reset)  # LIFO: runs before abort()
        stack.callback(load_ch.reset)

        _wait_for_event(source_ch, cancellation_event, ..., timeout)
        _wait_for_event(load_ch, cancellation_event, ..., timeout)

        for vin in vin_levels:
            source_ch.voltage_level = vin
            _wait_for_event(source_ch, cancellation_event, ..., timeout)
            for iout in iout_levels:
                if cancellation_event.is_set():
                    raise _MeasurementCancelledError()
                load_ch.current_level = iout
                _wait_for_event(load_ch, cancellation_event, ..., timeout)
                # ... measure and calculate ...
                vin_meas_list.append(...)
                eff_meas_list.append(...)
                yield (True, list(vin_meas_list), list(eff_meas_list), ...)
                # ^ intermediate: output_enabled=True, partial arrays

    # ExitStack has exited here: reset() called, outputs disabled.
    yield (False, vin_meas_list, eff_meas_list, ...)
    # ^ final: output_enabled=False, completed arrays
```

On cancellation inside the `with` block: ExitStack unwinds (`reset()` then `abort()`
as no-op on the now-Uncommitted sessions), then `_MeasurementCancelledError` propagates
out of the generator to `measure()`. On normal completion: ExitStack exits cleanly, then
the final yield delivers the completed results with `output_enabled=False`.

This structure produces exactly `N_vin × N_iout` intermediate yields plus 1 final yield.

`measure()` is the only place that touches `measurement_service.context`:

```python
def measure(...):
    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)
    # ^ gRPC framework calls this on both CANCELLED and DEADLINE_EXCEEDED
    ...
    try:
        return _run_measurement(..., cancellation_event=cancellation_event)
        # generator handler: yield from _run_measurement(..., cancellation_event=cancellation_event)
    except _MeasurementCancelledError:
        measurement_service.context.abort(grpc.StatusCode.CANCELLED, "Cancelled.")
```

In Layer 2 tests, pass a plain `threading.Event` — no gRPC service needed. Test
cancellation with `pytest.raises`:

```python
cancel = threading.Event()
cancel.set()
with pytest.raises(_MeasurementCancelledError):
    _run_measurement(..., cancellation_event=cancel)
    # generator handler: list(_run_measurement(..., cancellation_event=cancel))
```

### "Power On" mode and `initiate()` — see `nidcpower-patterns`

Whether to call `initiate()` with or without a context manager depends on whether
the mode must keep outputs active after returning. This is a nidcpower driver concern,
not an SDK concern — see the `nidcpower-patterns` skill (`initiate()` lifecycle section).
