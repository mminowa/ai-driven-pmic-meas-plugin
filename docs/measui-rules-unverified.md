# .measui Authoring Rules — Quick Reference

> **DISCLAIMER — Unverified / Empirical**
> Rules inferred from 13 official NI sample files in `measurement-plugin-python-examples-3.1.0.zip`
> ([github.com/ni/measurement-plugin-python](https://github.com/ni/measurement-plugin-python)).
> Not derived from a formal NI specification. Some rules confirmed empirically; many are
> unverified inferences. See [measui-authoring-guide-unverified.md](measui-authoring-guide-unverified.md)
> for full context.

---

## Parse errors (violations produce "The source file format is invalid")

- XML comments (`<!-- -->`) are rejected — delete all comments
- `Label` without `LabelOwner` causes parse error — standalone section-header labels are NOT supported
- Element `Id` must be 30–32 lowercase hex chars, no dashes (e.g. `a1000001000000000000000000000001`)
  - Exception: `Screen ClientId` uses brace UUID format `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`
- `ValueType="[Type]Boolean"` on `ChannelNumericText` → parse error; use `ChannelLED` instead
- Duplicate attributes on the same element → parse error
- Outer `PlotRenderer` (direct child of `ArrayGraph`): allowed attrs = `AreaBaseline BarBaseline Id PointFill PointShape xmlns` only — no `LineThickness`/`LineStroke`
- Inner `PlotRenderer` (inside `HmiGraphPlot`): allowed attrs = `Id LineStroke LineThickness PointFill xmlns` only — no `PointShape`/`AreaBaseline`/`BarBaseline`
- `Adjuster="[RangeAdjuster]FitData"` → parse error; use `FitExactly`
- Non-ASCII characters in attribute text values → parse error (use ASCII only)

---

## Control type → DataType mapping

| DataType | Writable input | Read-only output |
|---|---|---|
| `Boolean` | `ChannelCheckBox` or `ChannelSwitch` | `ChannelLED` |
| `Enum` | `ChannelEnumSelector` | `ChannelEnumSelector` + `InteractionMode="[SelectorInteractionModes]ReadOnly"` |
| `Double` / `Int32` etc. | `ChannelNumericText` | `ChannelNumericText` + `IsReadOnly="[bool]True"` |
| `DoubleArray1D` etc. | `ChannelArrayViewer` + `Enabled="[bool]True"` | `ChannelArrayViewer` (inner element + `IsReadOnly`) |
| `IOResourceArray1D` | `ChannelPinSelector` | — |
| `String` | `ChannelStringControl` | `ChannelStringControl` + `IsReadOnly="[bool]True"` |
| `Path` | `ChannelPathSelector` | — |
| `DoubleXYDataArray1D` | — | `ArrayGraph` + `HmiGraphPlot` |

---

## Channel binding format

```
[string]{<ClientId-uuid>}/Configuration/<DisplayName>   ← input parameter
[string]{<ClientId-uuid>}/Output/<DisplayName>           ← output value
```

- `<ClientId-uuid>` = value of `ClientId` on the `Screen` element (same UUID for every binding in the file)
- `<DisplayName>` must exactly match the string in `@measurement_service.configuration(...)` or `@measurement_service.output(...)` in `measurement.py`

---

## Namespace (xmlns) rules

Declare xmlns inline only where required — most elements inherit:

| Element | Requires explicit xmlns |
|---|---|
| `SourceFile` | `http://www.ni.com/PlatformFramework` |
| `Screen`, `ChannelPinSelector`, `ChannelEnumSelector` | `http://www.ni.com/InstrumentFramework/ScreenDocument` |
| `ScreenSurface` | `http://www.ni.com/ConfigurationBasedSoftware.Core` |
| `Label` | `http://www.ni.com/PanelCommon` |
| `RangeLabeledDivisions`, `GridLines`, `PlotRenderer`, `RingSelectorInfo` | `http://www.ni.com/Controls.LabVIEW.Design` |
| All other channel controls, graph elements | Inherit — no explicit xmlns needed |

---

## Key attribute syntax

| Value | Syntax |
|---|---|
| Float position/size | `[float]24` |
| Double (LineThickness) | `[double]2` |
| Integer | `[int]1` |
| Boolean | `[bool]True` / `[bool]False` |
| String | `[string]My Text` |
| Solid color (ARGB) | `[SMSolidColorBrush]#ffrrggbb` |
| Axis range | `[IRange]0, 100, System.Double` |
| Element cross-reference | `[UIModel]<32-char-hex-id>` |
| Enum `RingSelectorInfo` DisplayValue | Exact Python `IntEnum` member name (e.g. `POWER_ON_DUT`) |

---

## Checksum

Set `Checksum` on `SourceFile` to exactly **128 hex zeros** (placeholder — editor recomputes on save):

```
Checksum="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"
```

---

## Sample file reference

Hand-authoring some elements from scratch is impractical — copy the relevant block from the
official NI sample listed below and replace IDs, channel paths, and display names.

| What you need | Copy from |
|---|---|
| `ArrayGraph` + `ArrayGraphTools` (ComposableButton children) | `src/examples/meas-plugin/game_of_life/game_of_life.measui` |
| `SourceModelFeatureSet` block | any sample (all use the same version numbers) |
| `ChannelEnumSelector` + `RingSelectorInfo` | `src/examples/meas-plugin/nidmm_measurement/NIDmmMeasurement.measui` |
| `ChannelLED` | `src/examples/meas-plugin/output_voltage_measurement/OutputVoltageMeasurement.measui` |
| `ChannelArrayViewer` | `src/examples/meas-plugin/niscope_acquire_waveform/NIScope.measui` |
| `ChannelPinSelector` | `src/examples/meas-plugin/nidcpower_source_dc_voltage/NISourceDCVoltage.measui` |
| `ChannelCheckBox` / `ChannelSwitch` / `ChannelPathSelector` / `ChannelStringControl` | `src/examples/meas-plugin/sample_measurement/SampleMeasurement.measui` |

**Note on `Screen ClientId`:** `game_of_life.measui` omits `ClientId` on the `Screen` element
(newer editor format). When hand-authoring, always add `ClientId="{<uuid>}"` explicitly and
use the same UUID in all `Channel` bindings (see Channel binding format above).

---

## ChannelEnumSelector minimum template

```xml
<ChannelEnumSelector AdaptsToType="[bool]True" AllowNonSequentialValues="[bool]True"
    BaseName="[string]Enum" Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Enabled="[bool]True" Height="[float]24" Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False" Label="[UIModel]<label-id>"
    Left="[float]10" Top="[float]36" Value="[int]0" Width="[float]160"
    xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
  <RingSelectorInfo DisplayValue="[string]MEMBER_NAME" IsEnabled="[bool]True" Value="[int]0"
      xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
</ChannelEnumSelector>
```

## ChannelLED minimum template

```xml
<ChannelLED BaseName="[string]Round LED"
    Channel="[string]{<uuid>}/Output/<DisplayName>"
    ContentVisibility="[Visibility]Collapsed"
    FalseBackground="[SMSolidColorBrush]#ffe0e0e0" FalseContent="[string]Off"
    Height="[float]20" Id="<32-char-hex>" IsLabelBoundToChannel="[bool]False"
    IsReadOnly="[bool]True" Label="[UIModel]<label-id>"
    Left="[float]10" MinHeight="[float]20" MinWidth="[float]20"
    Shape="[LEDShape]Round" Top="[float]36"
    TrueBackground="[SMSolidColorBrush]#ff83ca9d" TrueContent="[string]On"
    Width="[float]20" />
```
