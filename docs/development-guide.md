# Development Guide

## Development Philosophy

This project follows **Specification-Driven Development (SDD)**, a disciplined approach where implementation is always preceded by a written specification. The goal is to make requirements explicit before code is written, which improves clarity, testability, and long-term maintainability.

### Workflow

```
 ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
 │  1. Specification│────▶│  2. Tests        │────▶│  3. Implementation│
 │  (docs/specs/)  │     │  (what to verify)│     │  (measurement.py)│
 └─────────────────┘     └─────────────────┘     └─────────────────┘
```

1. **Specification** — Document the test intent, inputs, outputs, instrument configuration, and expected behavior in `docs/specs/` before writing any code.
2. **Tests** — Define how the specification will be verified (expected ranges, edge cases, pass/fail criteria).
3. **Implementation** — Write `measurement.py` to satisfy the specification. Do not add logic not required by the spec.

No implementation work begins without a corresponding spec document.

## Framework Constraint

All measurement logic must be implemented as an **NI Measurement Plug-In** using the `ni_measurement_plugin_sdk` package. This framework:

- Exposes the measurement as a gRPC service discovered by NI InstrumentStudio
- Manages instrument sessions via pin maps and the NI session management service
- Provides a UI layer through `.measui` files

The generator command scaffolds the required project structure. It must be run via
Poetry so that it uses the project's own virtual environment:

```bash
poetry run ni-measurement-plugin-generator <MeasurementName>
```

`<MeasurementName>` is the display name of the measurement (e.g. `PMICEfficiency`) and
is independent of the plug-in directory name (`src/<measurement_name>`).

The generator creates a subdirectory named `<MeasurementName>/` inside the current
directory. Move the files up into the plug-in directory afterwards:

```bash
mv <MeasurementName>/* . && rmdir <MeasurementName>
```

Generated files that must not be removed:
- `measurement.py` — entry point; register configurations and outputs here
- `_helpers.py` — logging and CLI utilities
- `<MeasurementName>.measproj` — project file for Measurement Plug-In UI Editor
- `<MeasurementName>.measui` — UI definition
- `<MeasurementName>.serviceconfig` — service registration metadata
- `start.bat` — service launcher (Windows, calls `.venv\Scripts\python.exe measurement.py`)

The following files are **not** generated and must be added manually when using Poetry:

- `poetry.toml` — configures Poetry to create `.venv/` inside the project directory
- `install.bat` — used by the NI discovery service to install production dependencies (`poetry install --only main`)
- `.serviceignore` — excludes `.venv/` and `__pycache__/` when publishing to a plug-in library

## Dependency Management

Dependencies are managed with **Poetry**. The virtual environment must be created
**before** running the generator so that `ni-measurement-plugin-generator` runs
inside the project's own venv.

1. Create `pyproject.toml` manually with `ni_measurement_plugin_sdk`, `nidcpower`, and
   any other required packages. Use
   `src/examples/meas-plugin/nidcpower_source_dc_voltage/pyproject.toml` as a template.
2. Create `poetry.toml` to keep the virtual environment inside the project:

   ```toml
   [virtualenvs]
   in-project = true
   ```

3. Install dependencies (this creates `.venv/`):

   ```bash
   poetry install
   ```

4. Run the generator via Poetry (see **Framework Constraint** above).

   The `.venv/` created by `poetry install` is what `start.bat` uses to run the service.

## Project Structure

```
src/
  pmic_efficiency/              # Production plug-in
    measurement.py
    _helpers.py
    pyproject.toml
    poetry.toml                 # Added manually; keeps .venv inside the project
    PMICEfficiency.measproj
    PMICEfficiency.measui
    PMICEfficiency.serviceconfig
    PMICEfficiency.pinmap
    start.bat
    install.bat                 # Added manually; used by NI discovery service
    .serviceignore              # Added manually; excludes .venv and __pycache__ on publish
    .venv/                      # Created by `poetry install` (not committed)
  examples/
    meas-plugin/                # NI reference example (read-only reference)
    nidcpower/                  # Standalone nidcpower driver examples
docs/
  specs/                        # One Markdown file per test specification
  development-guide.md          # This file
  test-design.md                # Test strategy and test case definitions (Phase 2)
```

## Specification Document Format

Each spec file in `docs/specs/` should follow this structure:

```markdown
# <Test Name> Specification

## Purpose
What this measurement verifies and why.

## Instrument Configuration
| Role   | Pin Name | Instrument Type | Mode         |
|--------|----------|-----------------|--------------|
| Source | Vin_Pin  | PPS / SMU       | DC Voltage   |
| Sink   | Vout_Pin | Electronic Load / SMU | DC Current |

## Inputs (Configuration Parameters)
| Parameter       | Type   | Default | Description            |
|-----------------|--------|---------|------------------------|
| vin             | float  | 5.0 V   | Input voltage level    |
| iout_level      | float  | 1.0 A   | Output load current    |
| source_delay    | float  | 0.01 s  | Settling time          |

## Outputs
| Output      | Type        | Description                    |
|-------------|-------------|--------------------------------|
| efficiency  | float       | η = Pout / Pin × 100 (%)       |
| vin_meas    | float       | Measured input voltage (V)     |
| iin_meas    | float       | Measured input current (A)     |
| vout_meas   | float       | Measured output voltage (V)    |
| iout_meas   | float       | Measured output current (A)    |

## Test Flow
Step-by-step description of what the measurement does.
```

> Pass/fail judgment is the responsibility of the caller (TestStand or InstrumentStudio
> session), not the plug-in. Do not add pass/fail criteria to spec documents.
> Test cases and verification criteria belong in `docs/test-design.md`.

## Instrument Control Design

### Two-instrument topology

```
SMU/PPS  ──▶  PMIC input   |   PMIC output  ──▶  Electronic Load / SMU
(DC Voltage source)         |                     (DC Current sink)
Measures: Vin, Iin          |                     Measures: Vout, Iout
```

Both instruments are controlled via the `nidcpower` Python package. Each instrument is mapped to a named pin in the `.pinmap` file and reserved through the NI session management service.

### Efficiency calculation

```
Pin  = Vin_meas  × Iin_meas
Pout = Vout_meas × Iout_meas
η    = (Pout / Pin) × 100  [%]
```

### Simulation

All code must support instrument simulation for offline development and CI. Set the following environment variables (or add them to a `.env` file in the plug-in directory):

```
MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1
MEASUREMENT_PLUGIN_NIDCPOWER_BOARD_TYPE=PXIe
MEASUREMENT_PLUGIN_NIDCPOWER_MODEL=4141
```

## Coding Conventions

- Follow the patterns established in `src/examples/meas-plugin/nidcpower_source_dc_voltage/measurement.py`.
- Use `@measurement_service.configuration()` and `@measurement_service.output()` decorators to declare all inputs and outputs — do not use global state.
- Handle cancellation via `measurement_service.context.add_cancel_callback()`.
- Break long `wait_for_event()` calls into short polling loops to support cancellation (see `_wait_for_event()` in the reference example).
- No hardcoded resource names. All instrument addressing goes through the pin map.
- No confidential information. This repository is public.
