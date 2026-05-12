# CLAUDE.md

This file provides guidance for Claude Code when working on this project.

## Project Overview

This repository implements a **PMIC (Power Management IC) Efficiency Test Measurement Plug-In** using the NI Measurement Plug-Ins framework and Python. The plug-in measures the power conversion efficiency of a PMIC by sourcing input power with an NI PPS or SMU and sinking output load with an NI electronic load or SMU, both controlled via `nidcpower`.

## Development Approach

This project follows **Specification-Driven Development**:

1. **Specification first** — Write a formal spec (inputs, outputs, test flow, pass/fail criteria) before any implementation.
2. **Tests second** — Write tests that validate the spec before writing production code.
3. **Implementation last** — Implement only what the spec and tests require; no speculative features.

Do not implement anything not covered by a written specification in `docs/specs/`.

## Constraints

- **Framework**: All measurement logic must be implemented as an NI Measurement Plug-In using `ni_measurement_plugin_sdk`. Do not bypass this framework.
- **Instrument driver**: Use `nidcpower` for all PPS, SMU, and electronic load control.
- **Language**: Python 3.10+.
- **Documentation language**: All documentation, comments, and commit messages must be written in **English**.

## Repository Rules

- **No confidential information**: This is a public repository. Never commit credentials, internal hostnames, proprietary circuit parameters, or any customer/product-specific data.
- **No hardcoded resource names**: Instrument resource names (e.g., `PXI1Slot2`) must come from pin maps or configuration, not hardcoded in source.
- **Simulation support**: All code must be runnable with simulated instruments via the `MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1` env var, so CI and offline development work without hardware.

## Key Directories

```
src/
  pmic_efficiency/        # The PMIC efficiency measurement plug-in (to be created)
  examples/
    meas-plugin/          # NI reference example: nidcpower_source_dc_voltage
    nidcpower/            # Standalone nidcpower driver examples
docs/
  specs/                  # Formal specifications (written before implementation)
  development-guide.md    # Human-readable development process guide
```

## Hardware Targets

- **Input (source)**: NI PXIe-4151 (PPS) or any nidcpower-compatible SMU in DC voltage source mode
- **Output (sink)**: NI PXIe-4051 (electronic load) or any nidcpower-compatible SMU in DC current sink mode

## Plug-In Development Workflow

### 1. Install prerequisites

Install `ni_measurement_plugin_sdk` to get the generator command and the SDK:

```bash
python -m pip install ni_measurement_plugin_sdk nidcpower
```

### 2. Generate a new plug-in scaffold

Run the generator in the parent directory (`src/`) to create the initial project structure:

```bash
ni-measurement-plugin-generator <measurement_name>
```

This creates the following files inside a new `<measurement_name>/` directory:
- `measurement.py` — main measurement logic (edit this)
- `_helpers.py` — logging and CLI utilities
- `<measurement_name>.measproj` — project file for Measurement Plug-In UI Editor
- `<measurement_name>.measui` — UI definition
- `<measurement_name>.serviceconfig` — service registration config
- `start.bat` — service launcher (calls `.venv\Scripts\python.exe measurement.py`)

### 3. Configure pyproject.toml and add Poetry-related files

Add `nidcpower` and any other driver packages to `pyproject.toml` dependencies. Then manually create the following two files that the generator does not produce:

**`poetry.toml`** — keeps the virtual environment inside the project directory:

```toml
[virtualenvs]
in-project = true
```

**`install.bat`** — used by the NI discovery service to install dependencies:

```bat
@echo off
poetry install --only main
```

**`.serviceignore`** — excludes build artifacts when publishing the plug-in to a library:

```
.venv
__pycache__
```

### 4. Install dependencies with Poetry

```bash
cd <measurement_name>
poetry install
```

This creates a `.venv/` directory inside the plug-in folder, which `start.bat` uses to run the service.

### 5. Modify the generated files

Edit `measurement.py` to implement the measurement logic: configuration parameters, output definitions, and the `measure()` function. Update `.serviceconfig` and `.measui` as needed.

### 6. Run the measurement service

On Windows, run the generated batch file to start the gRPC service:

```bat
start.bat
```

### 7. Execute the measurement

Open `<measurement_name>.measui` in **Measurement Plug-In UI Editor**, then press the **Run** button.

### Simulation (no hardware required)

Create a `.env` file in the plug-in directory with:

```
MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1
MEASUREMENT_PLUGIN_NIDCPOWER_BOARD_TYPE=PXIe
MEASUREMENT_PLUGIN_NIDCPOWER_MODEL=4141
```

## Reference

- NI Measurement Plug-Ins (Python): https://www.ni.com/docs/ja-JP/bundle/measurementplugins/page/python-measurements.html
- Reference example: `src/examples/meas-plugin/nidcpower_source_dc_voltage/measurement.py`
- Electronic load example: `src/examples/nidcpower/nidcpower_sink_dc_current_into_electronic_load.py`
