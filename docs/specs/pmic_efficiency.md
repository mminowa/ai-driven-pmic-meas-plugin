# PMIC Efficiency Test Specification

## Purpose

Characterize the power conversion efficiency of a PMIC (Power Management IC) by sweeping both the input voltage (Vin) and the output load current (Iout). For each combination of Vin and Iout, the plug-in measures input and output voltage and current, calculates input power, output power, and conversion efficiency.

The plug-in supports three operating modes selectable at runtime:

| Mode | Python Enum Name | Description |
|---|---|---|
| **Perform Measurement** | `PERFORM_MEASUREMENT` (1) | Full Vin/Iout sweep with measurements and efficiency calculation |
| **Power on the DUT** | `POWER_ON_DUT` (0) | Configure instruments and enable outputs at initial setpoints; no measurement |
| **Power off the DUT** | `POWER_OFF_DUT` (2) | Reset both instruments to a known safe state and disable outputs |

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
| `measurement_mode` | Enum | `POWER_ON_DUT` | — | Operating mode: `POWER_ON_DUT` (0), `PERFORM_MEASUREMENT` (1), `POWER_OFF_DUT` (2) |
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

The measurement performs a two-dimensional sweep and streams partial results in real time via `yield`:

```
for each Vin in vin_levels:          # outer loop  [index i]
    set VIN pin to Vin (DC voltage source)
    for each Iout in iout_levels:    # inner loop  [index j]
        set VOUT pin to Iout (DC current sink)
        wait source_delay
        measure Vin_meas, Iin_meas on VIN pin
        measure Vout_meas, Iout_meas on VOUT pin
        calculate Pin, Pout, η
        append results to 1D measurement arrays
        append η to efficiency_measurements
        append (x=Iout, y=η) to efficiency[i]
        yield current state of all outputs   # real-time update
```

1D measurement array length after the full sweep: `len(vin_levels) × len(iout_levels)`.  
Ordering is row-major: all Iout values for `vin_levels[0]`, then all for `vin_levels[1]`, and so on.

`efficiency` (`DoubleXYData[]`) has length `len(vin_levels)`. Each element is built incrementally: within the inner loop, one `(x=Iout, y=η)` point is appended per Iout step. A yielded snapshot contains all points measured so far — partial curves for the current Vin row, complete curves for previous rows.

---

## Outputs

Status output:

| Output | Type | Description |
|---|---|---|
| `output_enabled` | Boolean | Reflects whether instrument outputs are currently active. Updated in real time during the flow: set to `True` immediately after outputs are enabled; set to `False` immediately after outputs are reset/disabled. `True` at the end of the flow only in `Power on the DUT` mode. |

Sweep-axis arrays (1D):

| Output | Type | Unit | Shape | Description |
|---|---|---|---|---|
| `vin_setpoints` | Double[] | V | `[N_vin]` | Vin setpoints — outer-loop (Vin) axis |
| `iout_setpoints` | Double[] | A | `[N_iout]` | Iout setpoints — inner-loop (Iout) axis; also the X values of each `efficiency` DoubleXYData element |

Measurement arrays (1D, length `N_vin × N_iout`, row-major order):

| Output | Type | Unit | Description |
|---|---|---|---|
| `vin_measurements` | Double[] | V | Measured input voltage |
| `iin_measurements` | Double[] | A | Measured input current |
| `pin_measurements` | Double[] | W | Calculated input power: `Pin = Vin_meas × Iin_meas` |
| `vout_measurements` | Double[] | V | Measured output voltage |
| `iout_measurements` | Double[] | A | Measured output current |
| `pout_measurements` | Double[] | W | Calculated output power: `Pout = Vout_meas × Iout_meas` |
| `efficiency_measurements` | Double[] | % | Conversion efficiency: `η = (Pout / Pin) × 100`. `NaN` when `Pin ≤ 0`. |

Efficiency graph output (DoubleXYData array):

| Output | Type | Unit | Description |
|---|---|---|---|
| `efficiency` | DoubleXYData[] | % | Conversion efficiency curves, one element per Vin level. X = `iout_setpoints` (A); Y = `η = (Pout / Pin) × 100` at each Iout. Length = `N_vin`. |

In **Power on the DUT** and **Power off the DUT** modes, all array outputs are yielded as empty arrays (single `yield`).

---

## Test Flow

All modes share the following common steps at the start and end.

**Common — Setup (all modes):**

1. Reserve instrument sessions for `VIN` (`source_pin`) and `VOUT` (`load_pin`) via the NI session management service.

2. Configure the `VIN` session (PPS / SMU):
   - Output function: `DC_VOLTAGE`
   - Voltage level range: `vin_voltage_level_range`
   - Voltage level: `source_initial_voltage`
   - Current limit: `vin_current_limit`
   - Current limit range: `vin_current_limit_range`
   - Source delay: `source_delay`
   - Aperture time: `aperture_time`
   - Sense: `source_sense`

3. Configure the `VOUT` session (Electronic Load / SMU):
   - Output function: `DC_CURRENT`
   - Current level: `load_initial_current`
   - Voltage limit range: `iout_voltage_limit_range`
   - Source delay: `source_delay`
   - Aperture time: `aperture_time`
   - Sense: `load_sense`

---

### Mode: Power on the DUT

4. Enable outputs on both sessions. Set `output_enabled = True`.
5. Wait for `SOURCE_COMPLETE` on both sessions.
6. Release instrument sessions.
7. **`yield`** empty array outputs (`output_enabled = True`).

The DUT is now powered at `source_initial_voltage` (VIN) and `load_initial_current` (VOUT). Outputs remain active.

---

### Mode: Perform Measurement

4. Enable outputs on both sessions. Set `output_enabled = True`. Wait for `SOURCE_COMPLETE` on each.

5. Initialize `efficiency` as a `DoubleXYData[]` of length `N_vin`; each element is a new, empty `DoubleXYData` object. Initialize all 1D measurement arrays and `efficiency_measurements` as empty lists.

6. For each `Vin` in `vin_levels` (outer loop, index `i`):
   a. Set `VIN` voltage level to `Vin`.
   b. Wait for `SOURCE_COMPLETE` event on `VIN`.
   c. For each `Iout` in `iout_levels` (inner loop, index `j`):
      - Check for cancellation.
      - Set `VOUT` current level to `Iout`.
      - Wait for `SOURCE_COMPLETE` event on `VOUT`.
      - Measure `Vin_meas`, `Iin_meas` from the `VIN` session.
      - Measure `Vout_meas`, `Iout_meas` from the `VOUT` session.
      - Calculate `Pin = Vin_meas × Iin_meas`.
      - Calculate `Pout = Vout_meas × Iout_meas`.
      - Calculate `η = (Pout / Pin) × 100`. If `Pin ≤ 0`, use `NaN`.
      - Append `Vin_meas`, `Iin_meas`, `Pin`, `Vout_meas`, `Iout_meas`, `Pout`, `η` to the corresponding 1D measurement arrays.
      - Append `x = Iout`, `y = η` to `efficiency[i]`.
      - **`yield` all current outputs** (partial results; `output_enabled = True`).

7. Reset both sessions to a known safe state (disable outputs). Set `output_enabled = False`.
8. Release instrument sessions.
9. **`yield` all output arrays** fully populated with measurement results (`output_enabled = False`).

> The `measure()` function is a generator. It uses `yield` (not `return`) to stream partial outputs after every Iout step. The final `yield` carries `output_enabled = False` and the completed arrays. The UI graph updates incrementally as each point arrives.

---

### Mode: Power off the DUT

4. Reset both sessions to a known safe state (disable outputs). Set `output_enabled = False`.
5. Release instrument sessions.
6. **`yield`** empty array outputs (`output_enabled = False`).

---

## UI Visualization

### Layout

The screen is **1280 × 940 pixels** with a fixed panel size. It is divided into two panes:

| Pane | Left | Top | Width | Height | Contents |
|---|---|---|---|---|---|
| Graph | 10 | 30 | 900 | 870 | Efficiency XY graph |
| Configuration | 940 | 10 | 330 | 920 | All input parameters + Output Enabled LED |

---

### Graph Pane (left)

`ArrayGraph` control bound to the `Efficiency` output (`DoubleXYDataArray1D`):

| Property | Value |
|---|---|
| Data source | `Efficiency` output (`DoubleXYData[]`) |
| X-axis label | Output Current (A) |
| X-axis scaling | Auto-fit to data |
| Y-axis label | Efficiency (%) |
| Y-axis range | Fixed 0 – 105 % |
| Series | One plot series per `DoubleXYData` element (one per Vin level) |
| Series line width | 2 px |
| Series colors | Six distinct NI colors (see table below) |
| Legend | Visible, positioned below the graph |
| Graph title | PMIC Efficiency vs. Output Current |
| Zoom/Pan toolbar | Displayed at top-right of the graph |

Series color palette (up to 6 Vin levels):

| Series index | Color | Hex (ARGB) |
|---|---|---|
| 0 | Red | `#ffff3030` |
| 1 | Blue | `#ff0080ff` |
| 2 | Green | `#ff00c000` |
| 3 | Orange | `#ffffa040` |
| 4 | Purple | `#ff8000ff` |
| 5 | Cyan | `#ff00c0c0` |

Because `measure()` yields after every Iout step, the graph updates in real time: curves grow point-by-point as the sweep progresses.

---

### Configuration Pane (right)

The right pane contains all input parameters and the `Output Enabled` status indicator, organized into four sections. **Note: section header labels (General, Source (VIN), Load (VOUT), Timing) are not implemented in the `.measui` file** — the NI parser rejects standalone `Label` elements without `LabelOwner`, making section headers unsupported.

#### Section: General

| Control | Type | Channel |
|---|---|---|
| Measurement Mode | Enum dropdown | `Configuration/Measurement Mode` |
| Source Pin | Pin selector (multi, IOResource) | `Configuration/Source Pin` |
| Load Pin | Pin selector (multi, IOResource) | `Configuration/Load Pin` |
| Output Enabled | Boolean LED (read-only) | `Output/Output Enabled` |

#### Section: Source (VIN)

| Control | Type | Channel |
|---|---|---|
| Vin Levels (V) | Numeric array input (3 rows visible, scrollable) | `Configuration/Vin Levels (V)` |
| Source Initial Voltage (V) | Numeric text | `Configuration/Source Initial Voltage (V)` |
| Vin Voltage Level Range (V) | Numeric text | `Configuration/Vin Voltage Level Range (V)` |
| Vin Current Limit (A) | Numeric text | `Configuration/Vin Current Limit (A)` |
| Vin Current Limit Range (A) | Numeric text | `Configuration/Vin Current Limit Range (A)` |
| Source Sense | Enum dropdown | `Configuration/Source Sense` |

#### Section: Load (VOUT)

| Control | Type | Channel |
|---|---|---|
| Iout Levels (A) | Numeric array input (3 rows visible, scrollable) | `Configuration/Iout Levels (A)` |
| Iout Voltage Limit Range (V) | Numeric text | `Configuration/Iout Voltage Limit Range (V)` |
| Load Initial Current (A) | Numeric text | `Configuration/Load Initial Current (A)` |
| Load Sense | Enum dropdown | `Configuration/Load Sense` |

#### Section: Timing

| Control | Type | Channel |
|---|---|---|
| Source Delay (s) | Numeric text | `Configuration/Source Delay (s)` |
| Aperture Time (s) | Numeric text | `Configuration/Aperture Time (s)` |

Channel paths above are relative to the service UUID prefix `{uuid}/`.

---

## Assumptions and Constraints

- Single-site operation only (multi-site is out of scope for this version).
- `vin_levels` and `iout_levels` must each contain at least one element (required only for `Perform Measurement` mode).
- `source_initial_voltage` must be a voltage the instrument can physically output (e.g., PXIe-4151 cannot output 0 V).
- `Pin` must be greater than zero for a valid efficiency result; if `Pin ≤ 0`, `efficiency` at that point is `NaN`.
- The plug-in does not manage PMIC power sequencing beyond the three modes described above; it assumes the DUT reaches steady state within `source_delay`.
- Simulation is supported via `MEASUREMENT_PLUGIN_NIDCPOWER_SIMULATE=1` (see [development-guide.md](../development-guide.md)).
