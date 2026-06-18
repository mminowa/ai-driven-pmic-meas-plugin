# .measui Grammar Reference

This is the lean reference for the *grammar* of NI's `.measui` (SFP XML) format — the
typed-attribute syntax, namespaces, channel binding, and ID rules that are tedious to
re-derive from samples each time. It is intentionally small; two larger paths carry the
rest:

- **Which control / XML to use for a data type → copy from a verified sample.** Run the
  `find-meas-example` skill (`.claude/skills/find-meas-example/find_example.sh <term>`).
  Do not transcribe per-control XML here; the samples are the source of truth and never drift.
- **What breaks the parser → [measui-gotchas.md](measui-gotchas.md)** (observed failures),
  then lint with `python scripts/validate_measui.py <file.measui>`.

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
| `[Type]` | `[Type]Double` | `ValueType`. Valid: `Double`, `Single`, `Int32`, `UInt32`, `UInt64`, `String` (not `Boolean` — see gotchas) |
| `[UIModel]` | `[UIModel]a100...0001` | Cross-reference to another element's `Id` |
| `[NI_Core_DataValues_TagRefnum]` | `[NI_Core_DataValues_TagRefnum]Pin1` | `SelectedResource` default pin on `ChannelPinSelector` |

### Colors (ARGB `#aarrggbb`)

| Prefix | Example | Notes |
|---|---|---|
| `[SMSolidColorBrush]` | `[SMSolidColorBrush]#ffffffff` | `BackgroundColor`, `LineStroke`, `PointFill`, etc. |
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
| `[RangeAdjuster]` | `FitExactly` | `Adjuster` on `ArrayGraphAxis` (`FitData` invalid — see gotchas) |
| `[FillBaseline]` | `Zero` | `AreaBaseline`, `BarBaseline` on `PlotRenderer` |
| `[PointShape]` | `Ellipse`, `Cross`, `Diamond`, `Rectangle` | `PointShape` on outer `PlotRenderer` |
| `[LEDShape]` | `Round` | `Shape` on `ChannelLED` |
| `[SwitchShape]` | `Slider` | `Shape` on `ChannelSwitch` |
| `[SelectorInteractionModes]` | `ReadOnly` | read-only `ChannelEnumSelector` output |
| `[PathSelectorInteractionModes]` | `BrowseDialog, TextInput` | `ChannelPathSelector` |
| `[MultipleSelectionModes]` | `List` | multi-select `ChannelPinSelector` |

---

## 6. Control ↔ DataType index

Quick index of which control to reach for. **For the actual XML, run the `find-meas-example`
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

## 7. Checksum

The `Checksum` on `SourceFile` must be present; its algorithm is unknown. Use 128 hex zeros
as a placeholder — the editor recomputes it on save through the GUI.

```
Checksum="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
```
