# Test Design

This document defines the testing strategy for the PMIC efficiency measurement plug-in
(Phase 2 of the Specification-Driven Development process). Tests are defined here before
implementation begins. Implementation must satisfy these test definitions.

---

## Key Constraint: Framework Separation

The `measure()` function in `measurement.py` is wrapped by
`@measurement_service.register_measurement` and runs inside a gRPC service context.
It cannot be called directly in a test without running the full service stack.

**Design principle**: Extract all logic that can be tested independently into pure
functions or helper functions that accept plain Python arguments. The `measure()` function
becomes a thin orchestrator that delegates to these testable units.

Concretely, the implementation must separate:

| Function | Responsibility | Testable without framework? |
|---|---|---|
| `_calculate_efficiency(pout, pin)` | Compute η or NaN | Yes — unit test |
| `_run_power_on(source_session, load_session, ...)` | Enable outputs | Yes — with nidcpower simulation |
| `_run_measurement(source_session, load_session, ...)` | Sweep and measure | Yes — with nidcpower simulation |
| `_run_power_off(source_session, load_session)` | Reset sessions | Yes — with nidcpower simulation |
| `measure(...)` | Dispatch to the above based on `measurement_mode` | No — requires gRPC context |

---

## Test Layers

### Layer 1 — Unit Tests

**Location**: `tests/test_calculations.py`
**Requirements**: `pytest` only; no hardware, no NI framework, no network.
**Run command**: `pytest tests/test_calculations.py`

These tests verify pure Python logic that contains no instrument or framework calls.

#### 1-1. Efficiency calculation — normal cases

| Input | Expected output |
|---|---|
| `pout=4.5, pin=5.0` | `90.0` |
| `pout=3.0, pin=4.0` | `75.0` |
| `pout=0.0, pin=5.0` | `0.0` |
| `pout=5.0, pin=5.0` | `100.0` |

#### 1-2. Efficiency calculation — Pin ≤ 0 (NaN guard)

| Input | Expected output |
|---|---|
| `pout=1.0, pin=0.0` | `NaN` |
| `pout=1.0, pin=-1.0` | `NaN` |
| `pout=0.0, pin=0.0` | `NaN` |

#### 1-3. Power calculation

| Input | Expected output |
|---|---|
| `voltage=5.0, current=1.0` | `5.0` W |
| `voltage=3.3, current=0.5` | `1.65` W |
| `voltage=0.0, current=1.0` | `0.0` W |

#### 1-4. Output array shape

Given `vin_levels` of length N and `iout_levels` of length M, all 2D output arrays
must have shape `[N, M]`.

| `vin_levels` | `iout_levels` | Expected shape |
|---|---|---|
| `[3.3, 5.0]` | `[0.5, 1.0, 1.5]` | `[2, 3]` |
| `[5.0]` | `[1.0]` | `[1, 1]` |
| `[3.3, 5.0, 12.0]` | `[0.5, 1.0, 2.0, 4.0]` | `[3, 4]` |

---

### Layer 2 — Integration Tests (nidcpower simulation)

**Location**: `tests/test_measurement.py`
**Requirements**: `pytest`, `nidcpower` with simulation options.
No real hardware. No NI session management service.
**Run command**: `pytest tests/test_measurement.py`

These tests call `_run_power_on()`, `_run_measurement()`, and `_run_power_off()`
directly with simulated `nidcpower` sessions.

Simulation options passed to `nidcpower.Session`:
```python
options = {"simulate": True, "driver_setup": {"Model": "4151", "BoardType": "PXIe"}}
```

#### 2-1. Power on the DUT

- `output_enabled` is `True` after the call.
- All array outputs are empty.
- No exception is raised.
- Sessions are released cleanly.

#### 2-2. Perform Measurement — output shapes

Given `vin_levels=[3.3, 5.0]` and `iout_levels=[0.5, 1.0, 1.5]`:

- All 2D output arrays have shape `[2, 3]`.
- `vin_setpoints` has length 2.
- `iout_setpoints` has length 3.
- `output_enabled` is `False` after the call.

#### 2-3. Perform Measurement — NaN handling

With simulated instruments, if `pin_measurements[i, j] ≤ 0`, then
`efficiency[i, j]` must be `NaN`, not `inf` or an exception.

#### 2-4. Perform Measurement — sweep order

`vin_setpoints` and `iout_setpoints` must match the input level lists in order.
`vin_setpoints[0]` must equal `vin_levels[0]`, and so on.

#### 2-5. Power off the DUT

- `output_enabled` is `False` after the call.
- All array outputs are empty.
- No exception is raised.
- Sessions are released cleanly.

#### 2-6. Cancellation during measurement

When the cancellation event is set during the inner sweep loop, the measurement
stops and both sessions are reset to a known safe state before returning.

---

### Layer 3 — Smoke Tests

**Location**: `tests/test_smoke.py`
**Requirements**: `pytest`; no hardware, no running service.
**Run command**: `pytest tests/test_smoke.py`

#### 3-1. Import

`import measurement` completes without error.

#### 3-2. Service config is valid JSON with required fields

`PMICEfficiency.serviceconfig` is valid JSON and contains:
- `services[0].displayName`
- `services[0].serviceClass`
- `services[0].providedInterfaces`
- `services[0].path`

#### 3-3. Required files exist

All of the following files exist in the plug-in directory:
- `measurement.py`
- `_helpers.py`
- `PMICEfficiency.measui`
- `PMICEfficiency.serviceconfig`
- `PMICEfficiency.pinmap`
- `start.bat`
- `install.bat`
- `.serviceignore`

---

### Layer 4 — Manual End-to-End Checklist

These tests require NI InstrumentStudio and the measurement service running via `start.bat`.
Run with simulated instruments using a `.env` file (see [CLAUDE.md](../CLAUDE.md)).

#### Service startup

- [ ] `start.bat` starts without error.
- [ ] The plug-in appears in InstrumentStudio's measurement list.

#### Power on the DUT mode

- [ ] `output_enabled` indicator shows `True` after run.
- [ ] All measurement array outputs are empty.
- [ ] Running a second time does not raise an error.

#### Perform Measurement mode

- [ ] All 2D output arrays are populated.
- [ ] XY Graph displays one efficiency curve per `vin_levels` entry.
- [ ] Each curve uses a distinct color.
- [ ] X-axis shows output current (A); Y-axis shows efficiency (%).
- [ ] `output_enabled` indicator shows `False` after run.

#### Power off the DUT mode

- [ ] `output_enabled` indicator shows `False` after run.
- [ ] All measurement array outputs are empty.

#### Sequential mode workflow

- [ ] Power on → Perform Measurement → Power off runs without error.
- [ ] `output_enabled` transitions: `False` → `True` → `False` → `False`.

---

## Simulation Caveat

Simulated `nidcpower` sessions do not return realistic voltage/current values.
Layer 2 integration tests therefore validate **structure and state**, not absolute
measurement accuracy:

- Array shapes and types are verified.
- `output_enabled` state transitions are verified.
- Numerical accuracy of efficiency values is verified only with real hardware
  (Layer 4 manual testing).

---

## Test File Structure

```
tests/
  test_calculations.py   # Layer 1: pure Python logic
  test_measurement.py    # Layer 2: nidcpower simulation
  test_smoke.py          # Layer 3: import and file existence
```

Layer 4 checklist is maintained in this document and executed manually before
each release.
