# Test Design

This document describes the four-layer testing strategy for NI Measurement Plug-In projects
following the Specification-Driven Development process. Tests are defined before implementation
begins. Implementation must satisfy these test definitions.

Each plugin's test cases are defined in `docs/specs/<plugin_name>_test_cases.md`.
For example: [docs/specs/pmic_efficiency_test_cases.md](specs/pmic_efficiency_test_cases.md).

---

## Key Constraint: Framework Separation

The `measure()` function in `measurement.py` is wrapped by
`@measurement_service.register_measurement` and runs inside a gRPC service context.
It cannot be called directly in a test without running the full service stack.

**Design principle**: Extract all logic that can be tested independently into pure
functions or helper functions that accept plain Python arguments. The `measure()` function
becomes a thin orchestrator that delegates to these testable units.

Concretely, separate the implementation into:

| Function category | Responsibility | Testable without framework? |
|---|---|---|
| Pure calculation functions | Compute derived values (e.g. efficiency, power) | Yes — unit test |
| Mode handler functions | Interact with instrument sessions for each operating mode | Yes — with simulated driver |
| `measure(...)` | Dispatch to the above based on the selected mode | No — requires gRPC context |

The specific function names for this project are listed in the test cases document.

---

## Test Layers

### Layer 1 — Unit Tests

**Location**: `tests/test_calculations.py`
**Requirements**: `pytest` only; no hardware, no NI framework, no network.
**Run command**: `pytest tests/test_calculations.py`

Test pure Python functions that contain no instrument or framework calls: calculations,
data transformations, and any other logic that can be exercised with plain Python arguments.

See the test cases document for the specific test cases for this project.

---

### Layer 2 — Integration Tests (simulated driver)

**Location**: `tests/test_measurement.py`
**Requirements**: `pytest` and the instrument driver with simulation options.
No real hardware. No NI session management service.
**Run command**: `pytest tests/test_measurement.py`

Call the mode handler functions directly with simulated driver sessions.
Verify output shapes, state transitions, and error handling without hardware.

See the test cases document for simulation options and test cases for this project.

---

### Layer 3 — Smoke Tests

**Location**: `tests/test_smoke.py`
**Requirements**: `pytest`; no hardware, no running service.
**Run command**: `pytest tests/test_smoke.py`

#### 3-1. Import

`import measurement` completes without error.

#### 3-2. Service config is valid JSON with required fields

The `.serviceconfig` file is valid JSON and contains:
- `services[0].displayName`
- `services[0].serviceClass`
- `services[0].providedInterfaces`
- `services[0].path`

#### 3-3. Required files exist

See the test cases document for the list of required files for this project.

---

### Layer 4 — Manual End-to-End Checklist

These tests require NI InstrumentStudio and the measurement service running via `start.bat`.
Run with simulated instruments using a `.env` file (see `docs/specs/<plugin_name>.md` →
Plugin Configuration for the required environment variables).

#### Service startup

- [ ] `start.bat` starts without error.
- [ ] The plug-in appears in InstrumentStudio's measurement list.

See the test cases document for the mode-specific checklist items for this project.

---

## Simulation Caveat

Simulated driver sessions do not return realistic values.
Layer 2 integration tests therefore validate **structure and state**, not absolute
measurement accuracy:

- Array shapes and types are verified.
- Output enabled/disabled state transitions are verified.
- Numerical accuracy is verified only with real hardware (Layer 4 manual testing).

---

## Test File Structure

```
tests/
  test_calculations.py   # Layer 1: pure Python logic
  test_measurement.py    # Layer 2: simulated driver
  test_smoke.py          # Layer 3: import and file existence
```

Layer 4 checklist is maintained in the test cases document and executed manually before
each release.
