# PMIC Efficiency — Test Cases

This document defines the test cases for the PMIC efficiency measurement plug-in
(Phase 2 of the Specification-Driven Development process). For the testing strategy
and layer definitions, see [docs/test-design.md](../test-design.md).

---

## Project-Specific Configuration

**Plug-in file prefix:** `PMICEfficiency`

**Layer 2 simulation options:**

```python
_SOURCE_OPTIONS = {"simulate": True, "driver_setup": {"Model": "4151", "BoardType": "PXIe"}}
_LOAD_OPTIONS   = {"simulate": True, "driver_setup": {"Model": "4051", "BoardType": "PXIe"}}
```

**Orchestration functions** (`measure()` dispatches to these):

| Function | Responsibility | Testable without framework? |
|---|---|---|
| `_calculate_power(voltage, current)` | Compute power (V × I) | Yes — unit test |
| `_calculate_efficiency(pout, pin)` | Compute η or NaN | Yes — unit test |
| `_run_power_on(source_session, load_session, ...)` | Enable outputs | Yes — with nidcpower simulation |
| `_run_measurement(source_session, load_session, ...)` | Sweep and measure | Yes — with nidcpower simulation |
| `_run_power_off(source_session, load_session)` | Reset sessions | Yes — with nidcpower simulation |
| `measure(...)` | Dispatch to the above based on `measurement_mode` | No — requires gRPC context |

---

## Layer 1 — Unit Test Cases

### 1-1. Efficiency calculation — normal cases

| Input | Expected output |
|---|---|
| `pout=4.5, pin=5.0` | `90.0` |
| `pout=3.0, pin=4.0` | `75.0` |
| `pout=0.0, pin=5.0` | `0.0` |
| `pout=5.0, pin=5.0` | `100.0` |

### 1-2. Efficiency calculation — Pin ≤ 0 (NaN guard)

| Input | Expected output |
|---|---|
| `pout=1.0, pin=0.0` | `NaN` |
| `pout=1.0, pin=-1.0` | `NaN` |
| `pout=0.0, pin=0.0` | `NaN` |

### 1-3. Power calculation

| Input | Expected output |
|---|---|
| `voltage=5.0, current=1.0` | `5.0` W |
| `voltage=3.3, current=0.5` | `1.65` W |
| `voltage=0.0, current=1.0` | `0.0` W |

---

## Layer 2 — Integration Test Cases

### 2-1. Power on the DUT

- `output_enabled` is `True` after the call.
- All array outputs are empty.
- No exception is raised.
- Sessions are released cleanly.

### 2-2. Perform Measurement — output shapes

Given `vin_levels=[3.3, 5.0]` and `iout_levels=[0.5, 1.0, 1.5]` (so `N_vin=2`, `N_iout=3`):

- All 1D measurement arrays have length `N_vin × N_iout = 6`, in row-major order
  (all Iout values for `vin_levels[0]`, then all for `vin_levels[1]`).
- `vin_setpoints` has length `N_vin` (2).
- `iout_setpoints` has length `N_iout` (3).
- `efficiency` (`DoubleXYData[]`) has length `N_vin` (2); each element holds `N_iout` (3) points.
- `output_enabled` is `False` after the call.

### 2-3. Perform Measurement — NaN handling

With simulated instruments, for the element at Vin index `i` and Iout index `j`
(flat row-major index `k = i * N_iout + j`): if `pin_measurements[k] ≤ 0`, then
`efficiency_measurements[k]` must be `NaN`, not `inf` or an exception.

### 2-4. Perform Measurement — sweep order

`vin_setpoints` and `iout_setpoints` must match the input level lists in order.
`vin_setpoints[0]` must equal `vin_levels[0]`, and so on.

### 2-5. Power off the DUT

- `output_enabled` is `False` after the call.
- All array outputs are empty.
- No exception is raised.
- Sessions are released cleanly.

### 2-6. Cancellation during measurement

When the cancellation event is set during the inner sweep loop, the measurement
stops and both sessions are reset to a known safe state before returning.

### 2-7. Intermediate yields stream partial results

`_run_measurement()` must yield once per Iout step (with `output_enabled=True`),
plus one final yield (with `output_enabled=False`) after the sweep completes.
For `N_vin` Vin levels and `N_iout` Iout levels, the total number of yields is
`N_vin × N_iout + 1`.

---

## Layer 3 — Smoke Test Cases

### 3-3. Required files exist

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

## Layer 4 — Manual End-to-End Checklist

### Power on the DUT mode

- [ ] `output_enabled` indicator shows `True` after run.
- [ ] All measurement array outputs are empty.
- [ ] Running a second time does not raise an error.

### Perform Measurement mode

- [ ] All 1D measurement arrays are populated.
- [ ] XY Graph displays one efficiency curve per `vin_levels` entry.
- [ ] Each curve uses a distinct color.
- [ ] X-axis shows output current (A); Y-axis shows efficiency (%).
- [ ] `output_enabled` indicator shows `False` after run.

### Power off the DUT mode

- [ ] `output_enabled` indicator shows `False` after run.
- [ ] All measurement array outputs are empty.

### Sequential mode workflow

- [ ] Power on → Perform Measurement → Power off runs without error.
- [ ] `output_enabled` transitions: `False` → `True` → `False` → `False`.
