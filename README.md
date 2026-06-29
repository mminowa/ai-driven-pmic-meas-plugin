# AI-Driven PMIC Efficiency Measurement Plug-In

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Python-based **Measurement Plug-In** for testing PMIC (Power Management IC) power conversion efficiency, built on the [NI Measurement Plug-Ins](https://www.ni.com/docs/en-US/bundle/measurementplugins/page/python-measurements.html) framework.

## Overview

This plug-in automates PMIC efficiency characterization by:

1. Sourcing a DC input voltage to the PMIC via an NI PPS or SMU
2. Sinking a DC load current from the PMIC output via an NI electronic load or SMU
3. Measuring input power (Vin × Iin) and output power (Vout × Iout)
4. Calculating power conversion efficiency: **η = Pout / Pin × 100%**

```
 NI PPS / SMU (source)          PMIC              NI Electronic Load / SMU (sink)
 ┌──────────────────┐      ┌──────────┐      ┌──────────────────────────────┐
 │  DC Voltage Out  │─────▶│  VIN  VOUT│─────▶│  DC Current Sink             │
 │  Current Measure │      └──────────┘      │  Voltage Measure             │
 └──────────────────┘                        └──────────────────────────────┘
      Pin = Vin × Iin                              Pout = Vout × Iout
                              η = Pout / Pin × 100%
```

## UI

<img src="docs/images/pmic-efficiency-ui.png" alt="PMIC Efficiency UI in NI InstrumentStudio" width="80%">

## Hardware Requirements

| Role | Example Hardware | Driver |
|---|---|---|
| Input power source | NI PXIe-4151 (PPS) or nidcpower-compatible SMU | NI-DCPower |
| Output load | NI PXIe-4051 (electronic load) or nidcpower-compatible SMU | NI-DCPower |

## Software Requirements

- Python 3.10+
- NI InstrumentStudio 2025 Q4 or later
- NI-DCPower driver
- `ni_measurement_plugin_sdk` Python package
- `nidcpower` Python package

## Getting Started

### 1. Install the plug-in

```bash
cd src/pmic_efficiency
install.bat
```

> `install.bat` runs `poetry install --only main`. [Poetry](https://python-poetry.org/docs/) must be installed and on your PATH.

### 2. Start the measurement service

```bash
start.bat
```

### 3. Run a measurement

Open `PMICEfficiency.measui` in **Measurement Plug-In UI Editor** and press **Run**.

### Simulation mode (no hardware required)

Create a `.env` file in `src/pmic_efficiency/` with the following content:

```
MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1
MEASUREMENT_PLUGIN_NIDCPOWER_BOARD_TYPE=PXIe
MEASUREMENT_PLUGIN_NIDCPOWER_MODEL=4151
```

Then start the service normally with `start.bat`.

## Repository Structure

```
src/
  pmic_efficiency/        # PMIC efficiency measurement plug-in
  examples/
    meas-plugin/          # NI Measurement Plug-In reference examples (multiple drivers)
    nidcpower/            # Standalone nidcpower driver examples
tests/
  pmic_efficiency/        # Unit and integration tests (Layers 1–3)
docs/
  specs/                  # Formal specifications, UI spec, and test cases
  test-design.md          # Four-layer test strategy (generic)
  update-measui.md        # Procedure for regenerating the .measui
.claude/                  # Claude Code automation: commands/, skills/, agents/
```

## Development

This project uses **Specification-Driven Development**. See [CLAUDE.md](CLAUDE.md) for the full development process and contribution guidelines.

### Automation (Claude Code)

If you work on this repo with [Claude Code](https://claude.com/claude-code), the three SDD
phases are automated by slash commands, run in order:

`/spec <name>` → `/test-cases <name>` → `/scaffold <name> <MeasurementName>` → `/implement <name>` → `/gen-measui <name>` → `/refine-measui <name>`

Phase 3 (Implementation) is split into four commands — `/scaffold`, `/implement`,
`/gen-measui`, `/refine-measui` — so each runs with a small, focused context.

Supporting tools (Claude invokes the skills and agent automatically when relevant):

- **Skills**
  - `find-meas-example` — find the verified sample for a given `DataType` / `.measui` control
  - `measurement-plugin-sdk` — `measurement.py` patterns and conventions
  - `measui-reference` — `.measui` grammar reference (namespaces, typed attributes, layout)
  - `measui-gotchas` — known `.measui` parser failures to avoid
  - `nidcpower-patterns` — nidcpower driver patterns that differ from standalone examples
- **Agent** — `spec-reviewer` reviews a draft spec against the project rules.

Each command, skill, and agent is self-documenting; see the files under `.claude/` for usage.

## License

[MIT License](LICENSE) © 2026 mminowa
