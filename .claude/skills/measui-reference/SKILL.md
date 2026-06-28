---
name: measui-reference
description: Grammar reference for NI's .measui (SFP XML) format — typed-attribute syntax, namespaces, channel binding, ID format, control heights, and layout patterns. Use when editing .measui XML directly.
---

# measui-reference

The *grammar* of NI's `.measui` (SFP XML) format — typed-attribute syntax, namespaces,
channel binding, ID rules, and layout patterns.

- **Which control / XML to use for a data type** → use the **find-meas-example** skill and
  copy from a verified sample. Do not transcribe per-control XML here; the samples are the
  source of truth and never drift.
- **What breaks the parser** → see the **measui-gotchas** skill.

> **Provenance.** Inferred from the 12 official NI samples in
> `measurement-plugin-python-examples-3.1.0.zip`
> ([github.com/ni/measurement-plugin-python](https://github.com/ni/measurement-plugin-python)),
> extracted under `src/examples/meas-plugin/`. Empirical, not a formal NI specification.

---

## 1. File structure

```
SourceFile                          (xmlns="http://www.ni.com/PlatformFramework")
  SourceModelFeatureSet             (namespace declarations + version metadata; copy as-is from the generator)
  Screen                            (xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument")
    ScreenSurface                   (xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core")
      <channel controls / graph>    (direct children of ScreenSurface — screen-relative coords)
      ScreenSurfaceCanvas           (optional panel container — children use canvas-relative coords)
```

- **SourceModelFeatureSet**: copy verbatim from `ni-measurement-plugin-generator` output;
  the version numbers are written at project-creation time.
- **Screen**: `ServiceClass` must match `serviceClass` in `.serviceconfig`. `ClientId` is the
  brace-UUID used by every `Channel` binding in the file (see §3).
- **ScreenSurface**: `PanelSizeMode="Fixed"` locks canvas size; coordinates are pixels.
- **Coordinate origin**: direct child of `ScreenSurface` = screen top-left; child of
  `ScreenSurfaceCanvas` = canvas top-left.

---

## 2. Namespace (xmlns) rules

Five namespaces appear across all samples. Each element either declares its own `xmlns`
inline or inherits from a parent that did. Declare explicitly only where required:

| Element | Requires explicit xmlns |
|---|---|
| `SourceFile`, `Image`, `FontSetting`, `Text` | `http://www.ni.com/PlatformFramework` |
| `Screen`, `ChannelPinSelector`, `ChannelEnumSelector` | `http://www.ni.com/InstrumentFramework/ScreenDocument` |
| `ScreenSurface` | `http://www.ni.com/ConfigurationBasedSoftware.Core` |
| `Label` | `http://www.ni.com/PanelCommon` |
| `RangeLabeledDivisions`, `GridLines`, `PlotRenderer`, `RingSelectorInfo` | `http://www.ni.com/Controls.LabVIEW.Design` |
| All other channel controls, graph elements, canvas | Inherit — no explicit xmlns |

---

## 3. Channel binding

Every data control links to a measurement parameter via its `Channel` attribute:

```
[string]{<service-uuid>}/Configuration/<DisplayName>   ← input parameter
[string]{<service-uuid>}/Output/<DisplayName>           ← output value
```

- `<service-uuid>` = the `ClientId` brace-UUID on the `Screen` element **in the same file**
  (`{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`). Every binding in one `.measui` uses the same
  UUID. It does **not** appear in `.serviceconfig` — the service link is via `ServiceClass`.
- `<DisplayName>` must **exactly** match the string in
  `@measurement_service.configuration("DisplayName", ...)` / `.output("DisplayName", ...)`
  in `measurement.py`, including spaces and capitalization.
- **Channel names** in `measurement.py` are always the snake_case Python parameter name;
  the human-readable label shown in the UI comes from `DisplayName`, not the channel name.

---

## 4. ID format

Element `Id` and `[UIModel]<id>` cross-references use **lowercase hex, no dashes**. Samples
contain 30–32-char IDs; **32 is the safe choice when hand-authoring**. Every ID must be
unique within the file.

```
a1000001000000000000000000000001        VALID (32 chars — recommended)
72b5606765b48f6a03e01d0505d78c9         VALID (31 chars — present in samples)
a1000001-0000-0000-0000-000000000001    INVALID (dashes not allowed)
```

**Exception — `Screen ClientId`** uses the brace-UUID format with dashes. All other `Id`
attributes use the dash-free hex format.

---

## 5. Attribute value type syntax

NI SFP XML uses typed attribute values with bracket prefixes. This is the core grammar.

### Primitives

| Prefix | Example | Notes |
|---|---|---|
| `[float]` | `[float]24` | Most numeric attributes (Left, Top, Width, Height) |
| `[double]` | `[double]1` | `LineThickness` in `HmiGraphPlot` `PlotRenderer` |
| `[int]` | `[int]1` | Rows, Columns, TabIndex, Value |
| `[uint]` | `[uint]1` | Alternate integer form (e.g. `Interval`) |
| `[bool]` | `[bool]True` | `True` / `False` |
| `[string]` | `[string]My Label` | Text; empty = `[string]` |

### References

| Prefix | Example | Notes |
|---|---|---|
| `[Type]` | `[Type]Double` | `ValueType`. Valid: `Double`, `Single`, `Int32`, `UInt32`, `UInt64`, `String` (not `Boolean` — see measui-gotchas) |
| `[UIModel]` | `[UIModel]a100...0001` | Cross-reference to another element's `Id` |
| `[NI_Core_DataValues_TagRefnum]` | `[NI_Core_DataValues_TagRefnum]Pin1` | `SelectedResource` default pin on `ChannelPinSelector` |

### Colors (ARGB `#aarrggbb`)

| Prefix | Example | Notes |
|---|---|---|
| `[SMSolidColorBrush]` | `[SMSolidColorBrush]#ffffffff` | `BackgroundColor`, `LineStroke`, `PointFill`, etc. Fully opaque prefix: `ff` |
| `[SMColor]` | `[SMColor]#00ffffff` | `Color` on `GridLines` only |

### Layout

| Prefix | Example | Notes |
|---|---|---|
| `[SMThickness]` | `[SMThickness]50,26,20,40` | left,top,right,bottom (no spaces) — `PlotAreaMargin` |
| `[IRange]` | `[IRange]0, 100, System.Double` | Axis range: min, max, type (spaces after commas) |
| `[ArrayElementIndex]` | `[ArrayElementIndex]0` | First visible index; 2D: `0,0` |

### Visibility / orientation / enums

| Prefix | Values | Used on |
|---|---|---|
| `[SMVisibility]` | `Visible`, `Collapsed` | `LabelVisibility`, `MinorTickVisibility`, … |
| `[Visibility]` | `Collapsed` | `ContentVisibility` (LED), `IndexVisibility` (array) |
| `[SMOrientation]` | `Horizontal`, `Vertical` | `Orientation` on array viewer, axis, switch |
| `[ScrollBarVisibility]` | `Auto`, `Hidden`, `Visible` | scroll-bar attributes |
| `[RenderMode]` | `Hardware` | `RenderMode` on `ArrayGraph` |
| `[RangeAdjuster]` | `FitExactly` | `Adjuster` on `ArrayGraphAxis` (`FitData` invalid — see measui-gotchas) |
| `[FillBaseline]` | `Zero` | `AreaBaseline`, `BarBaseline` on `PlotRenderer` |
| `[PointShape]` | `Ellipse`, `Cross`, `Diamond`, `Rectangle` | `PointShape` on outer `PlotRenderer` |
| `[LEDShape]` | `Round` | `Shape` on `ChannelLED` |
| `[SwitchShape]` | `Slider` | `Shape` on `ChannelSwitch` |
| `[SelectorInteractionModes]` | `ReadOnly` | read-only `ChannelEnumSelector` output |
| `[PathSelectorInteractionModes]` | `BrowseDialog, TextInput` | `ChannelPathSelector` |
| `[MultipleSelectionModes]` | `List` | multi-select `ChannelPinSelector` |

---

## 6. Control ↔ DataType index

Quick index of which control to reach for. **For the actual XML, use the find-meas-example
skill** and copy from the verified sample — do not author from memory.

| DataType | Output (read-only) | Input (writable) |
|---|---|---|
| `Boolean` | `ChannelLED` | `ChannelCheckBox` / `ChannelSwitch` |
| `Enum` | `ChannelEnumSelector` (`InteractionMode=ReadOnly`) | `ChannelEnumSelector` |
| `Double` / `Int32` / … | `ChannelNumericText` (`IsReadOnly`) | `ChannelNumericText` |
| `DoubleArray1D` / … | `ChannelArrayViewer` (inner `IsReadOnly`) | `ChannelArrayViewer` |
| `String` | `ChannelStringControl` (`IsReadOnly`) | `ChannelStringControl` |
| `IOResource(Array1D)` | — | `ChannelPinSelector` |
| `Path` | — | `ChannelPathSelector` |
| `DoubleXYData(Array1D)` | `ArrayGraph` + `HmiGraphPlot` | — |

**Enum binding correctness:** a `ChannelEnumSelector`'s `RingSelectorInfo` entries
(`DisplayValue` and `Value`) must **exactly match** the Python `IntEnum` member names and
integer values declared in `measurement.py` (sequential from 0, or set
`AllowNonSequentialValues="[bool]True"`). Mismatches bind silently to the wrong value.

The `ArrayGraphTools` zoom/pan toolbar contains `ComposableButton` children that are complex
and NI-generated — copy them verbatim from a generator output or sample rather than
hand-authoring.

---

## 7. Layout patterns

### Standard control heights (px)

| Control type | Height |
|---|---|
| Label | 15 |
| ChannelNumericText | 25 |
| ChannelEnumSelector | 24 |
| ChannelPinSelector | 25 |
| ChannelLED | 35 |
| ChannelArrayViewer (3 visible rows) | 95 |

### Vertical stacking inside a pane

```
Label      at Top = Y            (Height 15)
Control    at Top = Y + 18       (Height per table above)
Next label at Top = Y + 18 + control_height + 5
```

### Axis label (visible)

```xml
Label="[string]My Label" LabelVisibility="[SMVisibility]Visible"
```

### Fixed Y-axis range (no auto-scaling)

```xml
Adjuster="[RangeAdjuster]None" Range="[IRange]0, 105, System.Double"
```

### Auto-fit axis (scales to data)

```xml
Adjuster="[RangeAdjuster]FitExactly"
```

### Plot color and line thickness

```xml
LineStroke="[SMSolidColorBrush]#ffff3030"
PointFill="[SMSolidColorBrush]#ffff3030"
LineThickness="[double]2"
```

---

## 8. Checksum

The `Checksum` on `SourceFile` must be present; its algorithm is unknown. The Measurement
Plug-In UI Editor regenerates it on first save — do not try to compute it manually.

- **Editing an existing file**: leave the old value in place.
- **Authoring from scratch**: use 128 hex zeros as a placeholder.

```
Checksum="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
```
