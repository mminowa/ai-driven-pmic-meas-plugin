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

### 4. Run a measurement

Open `PMICEfficiency.measui` in **Measurement Plug-In UI Editor** and press **Run**.

### Simulation mode (no hardware required)

Create a `.env` file in `src/pmic_efficiency/` with the following content:

```
MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1
MEASUREMENT_PLUGIN_NIDCPOWER_BOARD_TYPE=PXIe
MEASUREMENT_PLUGIN_NIDCPOWER_MODEL=4141
```

Then start the service normally with `start.bat`.

## Repository Structure

```
src/
  pmic_efficiency/        # PMIC efficiency measurement plug-in
  examples/
    meas-plugin/          # NI reference example (nidcpower_source_dc_voltage)
    nidcpower/            # Standalone nidcpower driver examples
docs/
  specs/                  # Formal test specifications
  test-design.md          # Test strategy and test case definitions
```

## Development

This project uses **Specification-Driven Development**. See [CLAUDE.md](CLAUDE.md) for the full development process and contribution guidelines.

## License

[MIT License](LICENSE) © 2026 mminowa
