# PMIC Efficiency Test Specification

## Purpose

Characterize the power conversion efficiency of a PMIC (Power Management IC) by sweeping both the input voltage (Vin) and the output load current (Iout). For each combination of Vin and Iout, the plug-in measures input and output voltage and current, calculates input power, output power, and conversion efficiency.

No pass/fail judgment is made inside the plug-in. The caller (TestStand sequence or InstrumentStudio session) is responsible for any limit checking.

---

## Instrument Configuration

| Role | Pin Name | Default Instrument | nidcpower Output Function |
|---|---|---|---|
| Input power source | `VIN` | NI PXIe-4151 (PPS) | `DC_VOLTAGE` (source Vin, measure Iin) |
| Output load | `VOUT` | NI PXIe-4051 (Electronic Load) | `DC_CURRENT` (sink Iout, measure Vout) |

Both instruments are controlled via the `nidcpower` driver. Instrument-to-pin assignment is defined in the pin map; no resource names are hardcoded.

---

## Pin Map

A single-site pin map with two pins:

| Pin Name | Direction | Connected To |
|---|---|---|
| `VIN` | Source | PMIC input terminal |
| `VOUT` | Sink | PMIC output terminal |

Pin map file: `PMICEfficiency.pinmap`

---

## Inputs (Configuration Parameters)

| Parameter | Type | Default | Unit | Description |
|---|---|---|---|---|
| `source_pin` | IOResource | `VIN` | — | Pin connected to the PPS / SMU (input side) |
| `load_pin` | IOResource | `VOUT` | — | Pin connected to the electronic load / SMU (output side) |
| `vin_levels` | Double[] | `[3.3, 5.0]` | V | List of input voltage setpoints to sweep (outer loop) |
| `vin_current_limit` | Double | `2.0` | A | Current limit for the input PPS / SMU |
| `vin_current_limit_range` | Double | `2.0` | A | Current limit range for the input PPS / SMU |
| `vin_voltage_level_range` | Double | `6.0` | V | Voltage level range for the input PPS / SMU |
| `source_initial_voltage` | Double | `1.0` | V | Initial voltage applied to VIN before the sweep begins. Some instruments (e.g., PXIe-4151) cannot output 0 V; this value must be within the instrument's valid output range. |
| `source_sense` | Enum | `LOCAL` | — | Sense mode for the input PPS / SMU: `LOCAL` (2-wire) or `REMOTE` (4-wire) |
| `iout_levels` | Double[] | `[0.5, 1.0, 1.5, 2.0]` | A | List of output load current setpoints to sweep (inner loop) |
| `iout_voltage_limit_range` | Double | `6.0` | V | Voltage limit range for the electronic load / SMU |
| `load_initial_current` | Double | `0.1` | A | Initial current applied to VOUT before the sweep begins. Used to bring the electronic load to a known state before the first Iout setpoint. |
| `load_sense` | Enum | `LOCAL` | — | Sense mode for the electronic load / SMU: `LOCAL` (2-wire) or `REMOTE` (4-wire) |
| `source_delay` | Double | `0.01` | s | Settling time after applying each setpoint before measuring |
| `aperture_time` | Double | `0.01` | s | Measurement aperture time for both instruments |

---

## Sweep Structure

The measurement performs a two-dimensional sweep:

```
for each Vin in vin_levels:          # outer loop  [row index]
    set VIN pin to Vin (DC voltage source)
    for each Iout in iout_levels:    # inner loop  [column index]
        set VOUT pin to Iout (DC current sink)
        wait source_delay
        measure Vin_meas, Iin_meas on VIN pin
        measure Vout_meas, Iout_meas on VOUT pin
        calculate Pin, Pout, efficiency
        store results at [row, col] in 2D output arrays
```

Output array shape: `[len(vin_levels), len(iout_levels)]`
- Row index corresponds to `vin_levels`
- Column index corresponds to `iout_levels`

---

## Outputs

Sweep-axis arrays (1D):

| Output | Type | Unit | Shape | Description |
|---|---|---|---|---|
| `vin_setpoints` | Double[] | V | `[N_vin]` | Vin setpoints (row axis of the 2D arrays) |
| `iout_setpoints` | Double[] | A | `[N_iout]` | Iout setpoints (column axis of the 2D arrays) |

Measurement arrays (2D, shape `[N_vin, N_iout]`):

| Output | Type | Unit | Description |
|---|---|---|---|
| `vin_measurements` | Double[,] | V | Measured input voltage |
| `iin_measurements` | Double[,] | A | Measured input current |
| `pin_measurements` | Double[,] | W | Calculated input power: `Pin = Vin_meas × Iin_meas` |
| `vout_measurements` | Double[,] | V | Measured output voltage |
| `iout_measurements` | Double[,] | A | Measured output current |
| `pout_measurements` | Double[,] | W | Calculated output power: `Pout = Vout_meas × Iout_meas` |
| `efficiency` | Double[,] | % | Conversion efficiency: `η = (Pout / Pin) × 100` |

> 2D array output is supported from NI InstrumentStudio 2025 Q4.

---

## Test Flow

1. Reserve instrument sessions for `VIN` (`source_pin`) and `VOUT` (`load_pin`) via the NI session management service.

2. Configure the `VIN` session (PPS / SMU):
   - Output function: `DC_VOLTAGE`
   - Voltage level range: `vin_voltage_level_range`
   - Voltage level: `source_initial_voltage` (instrument-safe starting value)
   - Current limit: `vin_current_limit`
   - Current limit range: `vin_current_limit_range`
   - Source delay: `source_delay`
   - Aperture time: `aperture_time`
   - Sense: `source_sense`

3. Configure the `VOUT` session (Electronic Load / SMU):
   - Output function: `DC_CURRENT`
   - Current level: `load_initial_current` (safe starting value)
   - Voltage limit range: `iout_voltage_limit_range`
   - Source delay: `source_delay`
   - Aperture time: `aperture_time`
   - Sense: `load_sense`

4. Enable outputs on both sessions and wait for `SOURCE_COMPLETE` on each.

5. For each `Vin` in `vin_levels` (outer loop, row index `i`):
   a. Set `VIN` voltage level to `Vin`.
   b. Wait for `SOURCE_COMPLETE` event on `VIN`.
   c. For each `Iout` in `iout_levels` (inner loop, column index `j`):
      - Check for cancellation.
      - Set `VOUT` current level to `Iout`.
      - Wait for `SOURCE_COMPLETE` event on `VOUT`.
      - Measure `Vin_meas`, `Iin_meas` from the `VIN` session.
      - Measure `Vout_meas`, `Iout_meas` from the `VOUT` session.
      - Calculate `Pin = Vin_meas × Iin_meas`.
      - Calculate `Pout = Vout_meas × Iout_meas`.
      - Calculate `η = (Pout / Pin) × 100`. If `Pin ≤ 0`, store `NaN`.
      - Store all values at `[i, j]` in the 2D output arrays.

6. Reset both sessions to a known safe state.

7. Release instrument sessions.

8. Return all output arrays.

---

## UI Visualization

The `.measui` file shall include an XY Graph configured as follows:

| Property | Value |
|---|---|
| X-axis data | `iout_setpoints` (A) |
| Y-axis data | `efficiency` rows — one plot series per row (i.e., per Vin level) |
| Series color | Distinct color per Vin level |
| X-axis label | Output Current (A) |
| Y-axis label | Efficiency (%) |
| Legend | Labeled with the corresponding Vin setpoint value |
| Title | PMIC Efficiency vs. Output Current |

The result is a family of efficiency curves — one per Vin level — allowing visual comparison of efficiency across input voltage conditions.

---

## Assumptions and Constraints

- Single-site operation only (multi-site is out of scope for this version).
- `vin_levels` and `iout_levels` must each contain at least one element.
- `source_initial_voltage` must be a voltage the instrument can physically output (e.g., PXIe-4151 cannot output 0 V).
- `Pin` must be greater than zero for a valid efficiency result; if `Pin ≤ 0`, `efficiency` at that point is `NaN`.
- The plug-in does not manage PMIC power sequencing; it assumes the DUT reaches steady state within `source_delay`.
- Simulation is supported via `MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1` (see [development-guide.md](../development-guide.md)).
