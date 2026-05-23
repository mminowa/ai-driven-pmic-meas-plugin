# PMIC Efficiency UI Specification

This document describes the layout and controls of `PMICEfficiency.measui`.  
For the measurement logic, inputs, outputs, and test flow, see [pmic_efficiency.md](pmic_efficiency.md).

---

## Layout

The screen is **1280 × 940 pixels** with a fixed panel size. It is divided into two panes:

| Pane | Left | Top | Width | Height | Contents |
|---|---|---|---|---|---|
| Graph | 10 | 30 | 900 | 870 | Efficiency XY graph |
| Configuration | 940 | 10 | 330 | 920 | All input parameters + Output Enabled LED |

---

## Graph Pane (left)

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

## Configuration Pane (right)

The right pane contains all input parameters and the `Output Enabled` status indicator, organized into four sections. **Note: section header labels (General, Source (VIN), Load (VOUT), Timing) are not implemented in the `.measui` file** — the NI parser rejects standalone `Label` elements without `LabelOwner`, making section headers unsupported.

### Section: General

| Control | Type | Channel |
|---|---|---|
| Measurement Mode | Enum dropdown | `Configuration/Measurement Mode` |
| Source Pin | Pin selector (multi, IOResource) | `Configuration/Source Pin` |
| Load Pin | Pin selector (multi, IOResource) | `Configuration/Load Pin` |
| Output Enabled | Boolean LED (read-only) | `Output/Output Enabled` |

### Section: Source (VIN)

| Control | Type | Channel |
|---|---|---|
| Vin Levels (V) | Numeric array input (3 rows visible, scrollable) | `Configuration/Vin Levels (V)` |
| Source Initial Voltage (V) | Numeric text | `Configuration/Source Initial Voltage (V)` |
| Vin Voltage Level Range (V) | Numeric text | `Configuration/Vin Voltage Level Range (V)` |
| Vin Current Limit (A) | Numeric text | `Configuration/Vin Current Limit (A)` |
| Vin Current Limit Range (A) | Numeric text | `Configuration/Vin Current Limit Range (A)` |
| Source Sense | Enum dropdown | `Configuration/Source Sense` |

### Section: Load (VOUT)

| Control | Type | Channel |
|---|---|---|
| Iout Levels (A) | Numeric array input (3 rows visible, scrollable) | `Configuration/Iout Levels (A)` |
| Iout Voltage Limit Range (V) | Numeric text | `Configuration/Iout Voltage Limit Range (V)` |
| Load Initial Current (A) | Numeric text | `Configuration/Load Initial Current (A)` |
| Load Sense | Enum dropdown | `Configuration/Load Sense` |

### Section: Timing

| Control | Type | Channel |
|---|---|---|
| Source Delay (s) | Numeric text | `Configuration/Source Delay (s)` |
| Aperture Time (s) | Numeric text | `Configuration/Aperture Time (s)` |

Channel paths above are relative to the service UUID prefix `{uuid}/`.
