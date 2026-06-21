# CLAUDE.md

This file provides guidance for Claude Code when working on this project.

## Project-Specific Configuration

> When reusing this file for a new Measurement Plug-In project, update only this section.
> Everything below applies to any NI Measurement Plug-In built with this framework.

**What this plug-in measures:** PMIC (Power Management IC) power conversion efficiency — sweeps input voltage (Vin) and output load current (Iout) and calculates conversion efficiency at each operating point.

**Plug-in directory:** `src/pmic_efficiency/`

**Hardware targets:**

| Role | Instrument | Driver |
|---|---|---|
| Input power source | NI PXIe-4151 (PPS) or any nidcpower-compatible SMU | `nidcpower` |
| Output load | NI PXIe-4051 (Electronic Load) or any nidcpower-compatible SMU | `nidcpower` |

**Simulation environment variables** (create a `.env` file in the plug-in directory):

```
MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1
MEASUREMENT_PLUGIN_NIDCPOWER_BOARD_TYPE=PXIe
MEASUREMENT_PLUGIN_NIDCPOWER_MODEL=4151
```

**Driver-specific reference examples in this repo:**

- Measurement Plug-In example: `src/examples/meas-plugin/nidcpower_source_dc_voltage/`
- Standalone driver examples: `src/examples/nidcpower/`
- Electronic load example: `src/examples/nidcpower/nidcpower_sink_dc_current_into_electronic_load.py`

---

## Project Overview

This repository contains an NI Measurement Plug-In implemented with the NI Measurement Plug-Ins framework and Python. See **Project-Specific Configuration** above for what this particular plug-in measures and which instruments it targets.

## Development Approach

This project follows **Specification-Driven Development**. All work proceeds in three phases in order.

> These phases are automated by Claude Code slash commands (see `.claude/` and the
> Automation section in [README.md](README.md)). The commands delegate to the procedure
> documented here — this file remains the source of truth.

### Phase 1 — Specification

Write a formal spec in `docs/specs/` covering inputs, outputs, instrument configuration, test flow, and any constraints. Do not create any source files until the spec is complete and agreed upon.

> Automation: run `/spec <name>` (or `/new-plugin <name>` first to repurpose this template for a new measurement).

### Phase 2 — Test Definition

Define how the specification will be verified: expected value ranges, edge cases, and what constitutes correct behavior. Tests are written before production code.

> Automation: run `/test-cases <name>`.

### Phase 3 — Implementation

Set up the plug-in project, write `measurement.py` to satisfy the spec, and verify against the tests. See **Plug-In Technical Setup** below for the step-by-step procedure.

> Automation: Phase 3 is split into four commands run in order —
> `/scaffold <name> <MeasurementName>` → `/implement <name>` → `/gen-measui <name>` →
> `/refine-measui <name>`.

> Do not implement anything not covered by a written specification in `docs/specs/`.

## Constraints

- **Framework**: All measurement logic must be implemented as an NI Measurement Plug-In using `ni_measurement_plugin_sdk`. Do not bypass this framework.
- **Instrument driver**: Use the driver(s) listed in **Project-Specific Configuration**. Do not use alternative APIs or bypass the driver.
- **Language**: Python 3.10+.
- **Documentation language**: All documentation, comments, and commit messages must be written in **English**.

## Repository Rules

- **No confidential information**: This is a public repository. Never commit credentials, internal hostnames, proprietary circuit parameters, or any customer/product-specific data.
- **No hardcoded resource names**: Instrument resource names (e.g., `PXI1Slot2`) must come from pin maps or configuration, not hardcoded in source.
- **Simulation support**: All code must be runnable with simulated instruments using the env vars listed in **Project-Specific Configuration**, so CI and offline development work without hardware.

## Key Directories

```
src/
  <plugin_name>/          # The measurement plug-in (see Project-Specific Configuration)
  examples/               # NI reference examples (see Project-Specific Configuration for driver-specific paths)
docs/
  specs/                  # Formal specifications (written before implementation)
  test-design.md          # Test strategy and test case definitions (Phase 2)
```

## Plug-In Technical Setup

> **This section describes Phase 3 (Implementation) only.**
> Do not start these steps until the specification (`docs/specs/`) and test definitions are complete.

The steps below set up the Poetry virtual environment first so that
`ni-measurement-plugin-generator` runs inside the project's own venv.

### 0. Install Poetry and add it to PATH

For the latest installation instructions, refer to the **[official Poetry documentation](https://python-poetry.org/docs/)**.

**macOS / Linux / WSL / Git Bash:**

```bash
curl -sSL https://install.python-poetry.org | python3 -
export PATH="$HOME/.local/bin:$PATH"
poetry --version
```

Add the `export` line to your shell profile (e.g. `~/.bashrc` or `~/.zshrc`) to persist it.

**Windows (PowerShell):**

```powershell
py -3.12 -m pip install --user pipx
py -3.12 -m pipx ensurepath
pipx install poetry
poetry --version
```

> `py -3.12` requires Python 3.12. If you have a different version installed, replace `3.12` with your version (e.g. `py -3.11`). Open a new terminal after running `pipx ensurepath` for the PATH change to take effect.

### 1. Create the plug-in directory and pyproject.toml

Create the plug-in directory under `src/` and write `pyproject.toml` manually with
`ni_measurement_plugin_sdk`, the instrument driver package(s) listed in **Project-Specific Configuration**, and any other required packages as dependencies.
Use the reference example in `src/examples/meas-plugin/` as a template.

### 2. Add Poetry-related files

Create the following files in the plug-in directory (the generator does not produce them):

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

### 3. Install dependencies with Poetry

```bash
cd src/<measurement_name>
poetry install
```

This creates `.venv/` inside the plug-in directory. All subsequent commands
(including the generator) run from this virtual environment.

### 4. Generate the plug-in scaffold

Run the generator from inside the plug-in directory using the Poetry virtual environment:

```bash
poetry run ni-measurement-plugin-generator <MeasurementName>
```

The argument `<MeasurementName>` is the display name of the measurement (e.g. `PMICEfficiency`) and is independent of the plug-in directory name (`src/<measurement_name>`).

The generator creates a subdirectory named `<MeasurementName>/` containing the following files:
- `measurement.py` — main measurement logic (edit this)
- `_helpers.py` — logging and CLI utilities
- `<MeasurementName>.measproj` — project file for Measurement Plug-In UI Editor
- `<MeasurementName>.measui` — UI definition
- `<MeasurementName>.serviceconfig` — service registration config
- `start.bat` — service launcher (calls `.venv\Scripts\python.exe measurement.py`)

Move all generated files up into the plug-in directory and remove the now-empty subdirectory:

```bash
mv <MeasurementName>/* . && rmdir <MeasurementName>
```

### 5. Implement `measurement.py`

Edit `measurement.py` to implement the measurement logic: configuration parameters,
output definitions, and the `measure()` function. Update `.serviceconfig` as needed.

### 6. Build the UI (`.measui`)

To create or update `.measui`, follow the procedure in
[`docs/update-measui.md`](docs/update-measui.md). Re-run that procedure whenever
the `measurement.py` configuration parameters or outputs change in Step 5.

### 7. Run the measurement service

On Windows, run the generated batch file to start the gRPC service:

```bat
start.bat
```

### 8. Execute the measurement

Open `<measurement_name>.measui` in **Measurement Plug-In UI Editor**, then press the **Run** button.

### Simulation (no hardware required)

Create a `.env` file in the plug-in directory using the environment variables listed in
**Project-Specific Configuration**.

## Reference

- NI Measurement Plug-Ins (Python): https://www.ni.com/docs/ja-JP/bundle/measurementplugins/page/python-measurements.html
- Driver-specific reference examples: see **Project-Specific Configuration**
