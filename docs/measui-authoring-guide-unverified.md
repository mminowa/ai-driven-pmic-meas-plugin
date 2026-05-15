# NI Measurement Plug-In UI Editor — .measui Authoring Guide

> **DISCLAIMER — Unverified / Empirical**
>
> The rules in this guide are **inferred by pattern-matching across the 12 official NI
> sample `.measui` files** from
> [`measurement-plugin-python-examples-3.1.0.zip`](https://github.com/ni/measurement-plugin-python)
> (stored locally in `src/examples/meas-plugin/`). This is **not** derived from a
> formal NI specification of the SFP XML format. Rules described as causing parse
> errors are identified by the absence of the pattern in all 12 samples, not by
> exhaustive testing. Some rules have been confirmed empirically during development of
> `PMICEfficiency.measui`, but many remain unverified inferences. Treat this guide
> as a working hypothesis, not a specification.

This document captures everything learned about hand-authoring `.measui` files for NI
Measurement Plug-In UI Editor. It is intended as a reference when editing these files
outside the GUI editor.

**Verification status**: Partially empirical — see disclaimer above

**Source of truth**: 12 official NI sample files from `measurement-plugin-python-examples-3.1.0.zip` (`src/examples/meas-plugin/`)

---

## 1. What is a .measui file?

A `.measui` file is NI's proprietary **SFP (Screen File Package) XML** format. It defines
the user interface for a measurement plug-in service: which controls are displayed, how they
map to measurement parameters, and how plots are laid out.

The file is opened by **Measurement Plug-In UI Editor** (part of InstrumentStudio).
The NI parser performs strict semantic validation beyond plain XML well-formedness —
many valid XML constructs are rejected.

---

## 2. File structure

```
SourceFile                          (xmlns="http://www.ni.com/PlatformFramework")
  SourceModelFeatureSet             (namespace declarations + version metadata)
  Screen                            (xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument")
    ScreenSurface                   (xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core")
      ArrayGraph                    (graph widget — direct child of ScreenSurface, or inside a canvas)
      HmiChartPlotLegend            (direct child of ScreenSurface, or inside a canvas)
      ArrayGraphTools               (zoom/pan toolbar — direct child of ScreenSurface, or inside a canvas)
      ChannelPinSelector            (direct child of ScreenSurface, or inside a canvas)
      ChannelNumericText            (direct child of ScreenSurface, or inside a canvas)
      ChannelArrayViewer            (direct child of ScreenSurface, or inside a canvas)
      Label (standalone)            (direct child of ScreenSurface only — section headers)
      ScreenSurfaceCanvas           (panel container — direct child of ScreenSurface)
        ChannelNumericText          (canvas-relative coordinates)
        ChannelArrayViewer          (canvas-relative coordinates)
        Label (with LabelOwner)     (control labels — only LabelOwner labels allowed inside)
      Label (canvas title)          (direct child of ScreenSurface, LabelOwner -> canvas)
```

### 2.1 SourceModelFeatureSet

Copy this block **as-is** from the output of `ni-measurement-plugin-generator`. The version
numbers are written by the generator at project creation time and do not need to be updated
manually.

### 2.2 Screen element

```xml
<Screen ClientId="{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}"
        DisplayName="MyMeasurement" Id="<32-char-hex>" ServiceClass="MyMeasurement_Python"
        xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
```

`ServiceClass` must match the `serviceClass` field in `.serviceconfig`.

`ClientId` is a standard UUID in brace format. It is assigned by the generator or editor at
file creation time. **When hand-authoring a file that has `Channel` bindings, `ClientId` must
be present** — it is the UUID used in every `Channel` attribute in the file (see section 4).
Two NI-published samples omit `ClientId` (files saved by a newer editor version that tracks
the UUID internally), but for hand-authored files always include a freshly generated UUID here.

### 2.3 ScreenSurface element

```xml
<ScreenSurface BackgroundColor="[SMSolidColorBrush]#ffffffff" Height="[float]940"
               Id="<32-char-hex>" Left="[float]0" PanelSizeMode="Fixed"
               Top="[float]0" Width="[float]1280"
               xmlns="http://www.ni.com/ConfigurationBasedSoftware.Core">
```

`PanelSizeMode="Fixed"` locks the canvas size. Coordinates are in pixels.

`BackgroundColor` has two common values:

| Value | Use case |
|---|---|
| `[SMSolidColorBrush]#ffffffff` | Opaque white — standard for control panels |
| `[SMSolidColorBrush]#00ffffff` | Fully transparent — used by the NI-DCPower and Sample measurement examples (NI-SCOPE and NI-Digital SPI use `#ffffffff`) |

---

## 3. Element types and allowed attributes

### 3.1 Namespace summary

Exactly five namespaces appear across all NI sample `.measui` files:

| Namespace (short name) | Full URI |
|---|---|
| PlatformFramework | `http://www.ni.com/PlatformFramework` |
| ConfigurationBasedSoftware.Core | `http://www.ni.com/ConfigurationBasedSoftware.Core` |
| InstrumentFramework/ScreenDocument | `http://www.ni.com/InstrumentFramework/ScreenDocument` |
| PanelCommon | `http://www.ni.com/PanelCommon` |
| Controls.LabVIEW.Design | `http://www.ni.com/Controls.LabVIEW.Design` |

Each element either declares its own `xmlns` inline or inherits from a parent that declared it:

| Element | Required xmlns |
|---|---|
| `SourceFile` | PlatformFramework |
| `Image` | PlatformFramework |
| `FontSetting` | PlatformFramework |
| `Text` | PlatformFramework |
| `Screen` | InstrumentFramework/ScreenDocument |
| `ChannelPinSelector` | InstrumentFramework/ScreenDocument |
| `ChannelEnumSelector` | InstrumentFramework/ScreenDocument |
| `ScreenSurface` | ConfigurationBasedSoftware.Core |
| `ScreenSurfaceCanvas` | (inherits from `ScreenSurface` — no explicit xmlns needed) |
| `ChannelNumericText` | (inherits from `ScreenSurface` — no explicit xmlns needed) |
| `ChannelArrayViewer` | (inherits from `ScreenSurface` — no explicit xmlns needed) |
| `ChannelLED` | (inherits — no explicit xmlns needed) |
| `ChannelCheckBox` | (inherits — no explicit xmlns needed) |
| `ChannelSwitch` | (inherits — no explicit xmlns needed) |
| `ChannelStringControl` | (inherits — no explicit xmlns needed) |
| `ChannelPathSelector` | (inherits — no explicit xmlns needed) |
| `ArrayGraph` | (inherits — no explicit xmlns needed) |
| `ArrayGraphAxis` | (inherits — no explicit xmlns needed) |
| `ArrayGraphTools` | (inherits — no explicit xmlns needed) |
| `HmiGraphPlot` | (inherits — no explicit xmlns needed) |
| `HmiChartPlotLegend` | (inherits — no explicit xmlns needed) |
| `HmiChartCursorLegend` | (inherits — no explicit xmlns needed) |
| `HmiChartScaleLegend` | (inherits — no explicit xmlns needed) |
| `Label` | PanelCommon |
| `RangeLabeledDivisions` | Controls.LabVIEW.Design |
| `GridLines` | Controls.LabVIEW.Design |
| `PlotRenderer` | Controls.LabVIEW.Design |
| `RingSelectorInfo` | Controls.LabVIEW.Design |

`FontSetting` and `Text` appear only in the NI-Digital SPI sample and are uncommon in practice.

### 3.2 ScreenSurfaceCanvas

Optional visual grouping container. Controls can be placed either:

- **Directly inside `ScreenSurface`** — coordinates are screen-relative. No canvas needed.
  Several NI samples (`NIDmmMeasurement`, `SampleAllParameters`, etc.) use this approach exclusively.
- **Inside a `ScreenSurfaceCanvas`** — coordinates are **canvas-relative** (0,0 = canvas top-left).
  The canvas itself is positioned with screen-relative `Left`/`Top`.

Canvas is useful when you want a visible panel border and title label. It has no functional
effect on channel binding or parsing.

```xml
<ScreenSurfaceCanvas
    Background="[SMSolidColorBrush]#80808080"
    BackgroundColor="[SMSolidColorBrush]#ffe0e0e0"
    BaseName="[string]Canvas"
    Height="[float]820"
    Id="c1000001000000000000000000000001"
    Label="[UIModel]c1000002000000000000000000000002"
    Left="[float]770"
    Top="[float]120"
    Width="[float]500">
  <!-- channel controls and their LabelOwner Labels go here (canvas-relative coords) -->
</ScreenSurfaceCanvas>
<!-- title label: sibling of canvas in ScreenSurface, not inside it -->
<Label Height="[float]16" Id="c1000002000000000000000000000002"
       LabelOwner="[UIModel]c1000001000000000000000000000001"
       Left="[float]770" Text="[string]Configuration" Top="[float]100" Width="[float]100"
       xmlns="http://www.ni.com/PanelCommon" />
```

**Attribute notes:**
- `Background` — always `[SMSolidColorBrush]#80808080` in all samples (border color).
- `BackgroundColor` — optional. When present, always `[SMSolidColorBrush]#ffe0e0e0`
  (light grey fill). About half the NI samples omit it.
- `Label` — points to the title `Label` element that is a **sibling** in `ScreenSurface`,
  not a child of the canvas. The title `Label` must have `LabelOwner` pointing back to
  the canvas `Id`.
- A canvas with no children may be written as a self-closing tag (`/>`).

**Coordinate system summary:**

| Placement | Coord origin |
|---|---|
| Direct child of `ScreenSurface` | Screen top-left |
| Child of `ScreenSurfaceCanvas` | Canvas top-left |

### 3.3 ChannelNumericText

Numeric input or read-only output control.

```xml
<ChannelNumericText
    AdaptsToType="[bool]True"
    BaseName="[string]Numeric"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Enabled="[bool]True"
    Height="[float]24"
    Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    Top="[float]36"
    UnitAnnotation="[string]"
    ValueFormatter="[string]LV:G5"
    ValueType="[Type]Double"
    Width="[float]160" />
```

For read-only output display, add `IsReadOnly="[bool]True"` (omit `Enabled`).

**ValueType** — valid types confirmed across NI samples:

| Type | Example use |
|---|---|
| `[Type]Double` | Most numeric values |
| `[Type]Single` | Float parameters |
| `[Type]Int32` | Integer parameters |
| `[Type]UInt32` | Unsigned integer parameters |
| `[Type]UInt64` | Large unsigned integers |

`[Type]Boolean` is the only type not seen in any sample and may cause a parse error.

**ValueFormatter** — two forms are used interchangeably:
- Short: `[string]LV:G5` (5 significant digits, LabVIEW default)
- Long: `[string]DisplayFormat=Automatic:Digits=5:DigitDisplayType=SignificantDigits:MinimumFieldWidth=0:AlwaysShowSign=False:ShowThousandsSeparator=False`

**Optional attributes** present in some samples:
- `TabIndex="[int]N"` — keyboard tab order
- `Interval="[float]1"` or `Interval="[uint]1"` — spinner increment step
- `RadixBase="[RadixBase]0"` `RadixVisibility="[SMVisibility]Collapsed"` — radix display control
- `MinHeight="[float]N"` — minimum height constraint

**Optional child element** — `FontSetting` for custom font (e.g. large output displays):
```xml
<ChannelNumericText ...>
  <FontSetting FontFamily="Segoe UI" FontSize="24" Id="<32-char-hex>"
      xmlns="http://www.ni.com/PlatformFramework" />
</ChannelNumericText>
```

### 3.4 ChannelArrayViewer

Scrollable array input or output control.

**1D array (most common):**
```xml
<ChannelArrayViewer
    AdaptsToType="[bool]True"
    ArrayElement="[UIModel]<element-id>"
    BaseName="[string]Numeric Array Input"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Columns="[int]1"
    Dimensions="[int]1"
    Height="[float]72"
    Id="<32-char-hex>"
    IndexVisibility="[Visibility]Collapsed"
    IsFixedSize="[bool]False"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    Orientation="[SMOrientation]Vertical"
    Rows="[int]3"
    Top="[float]150"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Visible"
    Width="[float]104">
  <p.DefaultElementValue>0x0</p.DefaultElementValue>
  <ChannelArrayNumericText BaseName="[string]Numeric" Height="[float]24"
      Id="<element-id>"
      UnitAnnotation="[string]" ValueFormatter="[string]LV:G5"
      ValueType="[Type]Double" Width="[float]72" />
</ChannelArrayViewer>
```

**2D array** — add `Dimensions="[int]2"`, set `Columns` > 1, use
`Orientation="[SMOrientation]Horizontal"`, and include `FirstIndex`:
```xml
<ChannelArrayViewer ... Columns="[int]3" Dimensions="[int]2"
    FirstIndex="[ArrayElementIndex]0,0"
    Orientation="[SMOrientation]Horizontal" ...>
```

For read-only output arrays, add `IsReadOnly="[bool]True"` to the inner element.

For writable input arrays, add `Enabled="[bool]True"` to the `ChannelArrayViewer`.

**Optional attributes:** `IsFixedSize="[bool]False"` (present in 8/10 NI samples),
`TabIndex="[int]N"`, `FirstIndex` (1D: `[ArrayElementIndex]0`).

**Array element types** — replace the inner `ChannelArrayNumericText` with the appropriate
type for the parameter's data type:

| Inner element | Use for |
|---|---|
| `ChannelArrayNumericText` | Numeric arrays (`Double`, `Int32`, etc.) |
| `ChannelArrayStringControl` | String arrays |

`ChannelArrayStringControl` takes the same attributes as `ChannelArrayNumericText` minus
`ValueType`, `ValueFormatter`, and `UnitAnnotation`:
```xml
<ChannelArrayStringControl AcceptsReturn="[bool]False" BaseName="[string]String"
    Height="[float]24" HorizontalScrollBarVisibility="[ScrollBarVisibility]Hidden"
    Id="<element-id>" IsReadOnly="[bool]True"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Auto" Width="[float]72" />
```
Also set `<p.DefaultElementValue>""</p.DefaultElementValue>` (empty string) instead of `0x0`.

### 3.5 ChannelPinSelector

Pin/resource selector. Can be placed in `ScreenSurface` directly or inside a
`ScreenSurfaceCanvas`.

```xml
<ChannelPinSelector
    AllowUndefinedValues="[bool]True"
    BaseName="[string]Pin"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    DataType="[Type]String"
    Enabled="[bool]True"
    Height="[float]24"
    Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]20"
    Top="[float]36"
    Width="[float]136"
    xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument" />
```

**Optional attributes:**
- `SelectedResource="[NI_Core_DataValues_TagRefnum]<PinName>"` — default pin shown before
  the measurement runs (8/11 NI samples include this; omit if no sensible default).
- `MultipleSelectionMode="[MultipleSelectionModes]List"` — enables selecting multiple pins;
  only required for parameters that accept a list of pins (4/11 samples use it).

### 3.6 Label

Labels serve two roles determined by whether `LabelOwner` is present:

**Control label** (`LabelOwner` present — pairs with a specific control):
```xml
<Label Height="[float]16" Id="<32-char-hex>"
       LabelOwner="[UIModel]<control-id>"
       Left="[float]10" Text="[string]My Control" Top="[float]20" Width="[float]120"
       xmlns="http://www.ni.com/PanelCommon" />
```
Coordinates follow the same origin as the paired control (canvas-relative if inside a canvas,
screen-relative otherwise). Can be placed inside or outside a canvas.

**Standalone label** (no `LabelOwner`): **NOT SUPPORTED — causes a parse error.**

All 12 NI sample files contain zero `Label` elements without `LabelOwner`. The NI parser
rejects any `Label` that lacks `LabelOwner`. If you need section header text, the only
supported approach is a canvas title label (a `Label` with `LabelOwner` pointing to a
`ScreenSurfaceCanvas`). There is no equivalent for inline section headers between controls.

**Height** — NI samples use either `[float]14` or `[float]16` for label height. Both work.

### 3.7 ArrayGraph

XY graph widget. Must be a direct child of `ScreenSurface`.

```xml
<ArrayGraph
    Background="[SMSolidColorBrush]#00000000"
    BaseName="[string]Array Graph"
    Height="[float]300"
    Id="<32-char-hex>"
    Label="[UIModel]<title-label-id>"
    Left="[float]10"
    MinWidth="[float]230"
    PlotAreaMargin="[SMThickness]50,26,20,40"
    PreferIndexData="[bool]False"
    RenderMode="[RenderMode]Hardware"
    SuppressScaleLayout="[bool]False"
    Top="[float]30"
    Width="[float]500">
  <ArrayGraphAxis ... />   <!-- horizontal (X) axis -->
  <ArrayGraphAxis ... />   <!-- vertical (Y) axis -->
  <PlotRenderer ... />     <!-- one per series — defines color/style palette -->
  <HmiGraphPlot ... />     <!-- one per data channel — binds data to axes -->
</ArrayGraph>
```

`Background` is optional (4/5 NI samples include it, always `#00000000` transparent).
`Label` references a sibling `<Label>` element in `ScreenSurface` for the graph title.

#### ArrayGraphAxis

```xml
<ArrayGraphAxis
    Adjuster="[RangeAdjuster]FitExactly"
    Id="<32-char-hex>"
    Label="[string]My Axis (units)"
    LabelVisibility="[SMVisibility]Visible"
    MajorDivisions="[UIModel]<divisions-id>"
    Orientation="[SMOrientation]Horizontal"
    Range="[IRange]0, 100, System.Double"
    ValueType="[Type]Double">
  <RangeLabeledDivisions Id="<32-char-hex>"
      xmlns="http://www.ni.com/Controls.LabVIEW.Design">
    <p.LabelPresenter Format="G6" />
  </RangeLabeledDivisions>
</ArrayGraphAxis>
```

- `Adjuster`: use `FitExactly` (`FitData` is invalid).
- `Range`: format is `[IRange]min, max, System.Double`.
- `Orientation`: `Horizontal` (X axis) or `Vertical` (Y axis).
- `MajorDivisions` is required — references a `RangeLabeledDivisions` child by ID.
- `MinorTickVisibility` — optional (5/10 samples include it).
- `MajorGridLines` — optional reference to a `GridLines` child (only 1/10 samples use it).

**`RangeLabeledDivisions`** — minimal form (Id + xmlns) is most common. The optional
`<p.LabelPresenter Format="G6" />` child controls tick label formatting; G6 is the standard
value in all NI samples (the guide previously showed G4, which was wrong).
`LabelVisibility`, `Mode`, and `TickVisibility` attributes are all optional.

**`GridLines`** — rarely used (only 1 NI sample). Omit unless grid lines are required:
```xml
<GridLines Color="[SMColor]#00ffffff" Id="<32-char-hex>"
    xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
```

#### PlotRenderer (direct child of ArrayGraph — color/style palette entry)

```xml
<PlotRenderer AreaBaseline="[FillBaseline]Zero" BarBaseline="[FillBaseline]Zero"
    Id="<32-char-hex>" PointFill="[SMSolidColorBrush]#ffff3030"
    PointShape="[PointShape]Ellipse"
    xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
```

Valid attributes: `AreaBaseline`, `BarBaseline`, `Id`, `PointFill`, `PointShape`, `xmlns`.
Do **not** add `LineThickness`, `LineStroke`, or `LineStyle` here.

#### HmiGraphPlot (data binding)

```xml
<HmiGraphPlot
    Channel="[string]{<uuid>}/Output/<DisplayName>"
    HorizontalScale="[UIModel]<x-axis-id>"
    Id="<32-char-hex>"
    IsDefaultPlot="[bool]False"
    Label="[string]Series Name"
    VerticalScale="[UIModel]<y-axis-id>">
  <PlotRenderer Id="<32-char-hex>"
      LineStroke="[SMSolidColorBrush]#ffea4225"
      LineThickness="[double]1"
      xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
</HmiGraphPlot>
```

The inner `PlotRenderer` (inside `HmiGraphPlot`) controls the rendered line style.
Valid attributes: `Id`, `LineStroke`, `LineThickness`, `PointFill`, `xmlns`.
- `LineStroke` — line color (7/8 NI samples); use `[SMSolidColorBrush]#ffrrggbb`.
- `LineThickness` — line width in pixels (all 8 samples).
- `PointFill` — point color when `PointShape` is set (rare, 1/8 samples).
Do **not** add `PointShape`, `AreaBaseline`, or `BarBaseline` here.

### 3.8 ChannelEnumSelector

Dropdown for enum input/output. Use this instead of `ChannelNumericText` for
`DataType.Enum` parameters — it shows human-readable names, not numbers.
Can be placed in `ScreenSurface` directly or inside a `ScreenSurfaceCanvas`.

**Input (writable):**
```xml
<ChannelEnumSelector
    AdaptsToType="[bool]True"
    AllowNonSequentialValues="[bool]True"
    BaseName="[string]Enum"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Enabled="[bool]True"
    Height="[float]24"
    Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    Top="[float]36"
    Value="[int]0"
    Width="[float]136"
    xmlns="http://www.ni.com/InstrumentFramework/ScreenDocument">
  <RingSelectorInfo DisplayValue="[string]Option A" IsEnabled="[bool]True" Value="[int]0"
      xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
  <RingSelectorInfo DisplayValue="[string]Option B" IsEnabled="[bool]True" Value="[int]1"
      xmlns="http://www.ni.com/Controls.LabVIEW.Design" />
</ChannelEnumSelector>
```

**Output (read-only):** replace `Enabled`, `IsLabelBoundToChannel`, and `Value` with
`InteractionMode="[SelectorInteractionModes]ReadOnly"`. Bind to `/Output/<DisplayName>`.

- `Value="[int]N"` sets the default selected index shown before the first measurement run.
- `RingSelectorInfo` entries must exactly match the enum member names and integer values
  defined in `measurement.py`. The `Value` integers must be sequential starting from 0
  (or non-sequential if `AllowNonSequentialValues="[bool]True"`).
- The element closes with `</ChannelEnumSelector>` (not self-closing) even when it contains
  no children — some samples omit children and use an empty tag pair.

### 3.9 ChannelLED

Read-only boolean output indicator. Can be placed in `ScreenSurface` or inside a canvas.
No explicit xmlns needed (inherits).

```xml
<ChannelLED
    BaseName="[string]Round LED"
    Channel="[string]{<uuid>}/Output/<DisplayName>"
    ContentVisibility="[Visibility]Collapsed"
    FalseBackground="[SMSolidColorBrush]#ffe0e0e0"
    FalseContent="[string]Off"
    Height="[float]20"
    Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False"
    IsReadOnly="[bool]True"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    MinHeight="[float]20"
    MinWidth="[float]20"
    Shape="[LEDShape]Round"
    Top="[float]36"
    TrueBackground="[SMSolidColorBrush]#ff83ca9d"
    TrueContent="[string]On"
    Width="[float]20" />
```

- `ContentVisibility="[Visibility]Collapsed"` hides the On/Off text label inside the LED,
  showing only the color. Set to `Visible` to show text inside the LED shape.
- `FalseBackground` — color when the output value is `False` (typically grey or dark green).
- `TrueBackground` — color when the output value is `True` (optional; 1/3 NI samples omit it,
  leaving the True color at its default).
- `Shape="[LEDShape]Round"` is the only shape observed in NI samples.

### 3.10 ChannelCheckBox

Writable boolean input control. Can be placed in `ScreenSurface` or inside a canvas.
No explicit xmlns needed (inherits).

```xml
<ChannelCheckBox
    BaseName="[string]Checkbox"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Content="[string]Off/On"
    Enabled="[bool]True"
    Height="[float]16"
    Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    MinHeight="[float]16"
    MinWidth="[float]16"
    Top="[float]36"
    Width="[float]16" />
```

- `Content` — text shown beside the checkbox. Set `ContentVisibility="[Visibility]Collapsed"`
  to hide it when you use a separate `Label` element instead.
- `Width` — set wider than 16 if `Content` text should be visible (e.g. `[float]87`).

### 3.11 ChannelSwitch

Writable boolean input control rendered as a physical toggle switch. Can be placed in
`ScreenSurface` or inside a canvas. No explicit xmlns needed (inherits).

```xml
<ChannelSwitch
    BaseName="[string]Switch"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Enabled="[bool]True"
    FalseContent="[string]Open"
    Height="[float]50"
    Id="<32-char-hex>"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    MinHeight="[float]24"
    MinWidth="[float]12"
    Orientation="[SMOrientation]Vertical"
    Shape="[SwitchShape]Slider"
    Top="[float]36"
    TrueContent="[string]Close"
    Width="[float]63" />
```

- `FalseContent` / `TrueContent` — labels for the two states.
- `Shape="[SwitchShape]Slider"` is the only shape observed in NI samples.
- `Orientation` — `Vertical` (default) or `Horizontal`.

### 3.12 ChannelStringControl

String input or read-only output control. Can be placed in `ScreenSurface` or inside a
canvas. No explicit xmlns needed (inherits).

```xml
<ChannelStringControl
    AcceptsReturn="[bool]False"
    BaseName="[string]String"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Enabled="[bool]True"
    Height="[float]24"
    HorizontalScrollBarVisibility="[ScrollBarVisibility]Hidden"
    Id="<32-char-hex>"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    Text="[string]"
    Top="[float]36"
    VerticalScrollBarVisibility="[ScrollBarVisibility]Auto"
    Width="[float]160" />
```

For read-only output, replace `Enabled="[bool]True"` and `Text` with
`IsReadOnly="[bool]True"` and bind to `/Output/<DisplayName>`.

- `Text="[string]"` — default value shown before the first run (input only; omit for output).
- `AcceptsReturn="[bool]False"` — prevents multi-line input (all NI samples set this).

### 3.13 ChannelPathSelector

File path input control with a browse-dialog button. Can be placed in `ScreenSurface` or
inside a canvas. No explicit xmlns needed (inherits).

```xml
<ChannelPathSelector
    BaseName="[string]Path"
    Channel="[string]{<uuid>}/Configuration/<DisplayName>"
    Enabled="[bool]True"
    FilterLabel="[null]"
    FilterPatterns="[null]"
    Height="[float]24"
    Id="<32-char-hex>"
    InteractionMode="[PathSelectorInteractionModes]BrowseDialog, TextInput"
    IsLabelBoundToChannel="[bool]False"
    Label="[UIModel]<label-id>"
    Left="[float]10"
    Top="[float]36"
    Width="[float]136"
    WrapText="[bool]False" />
```

- `FilterLabel` / `FilterPatterns` — file type filter for the browse dialog. All NI samples
  use `[null]` (no filter). To restrict to specific extensions, provide a display label and
  a glob pattern (e.g. `FilterPatterns="[string]*.tdms"`).
- `InteractionMode="[PathSelectorInteractionModes]BrowseDialog, TextInput"` — allows both
  typing a path and clicking the browse button. All NI samples use this value.

### 3.14 Graph accessory widgets

These widgets are always paired with an `ArrayGraph` via a `Graph="[UIModel]<graph-id>"`
reference. All are direct children of `ScreenSurface` or inside a canvas (same rules as
other channel controls). None require an explicit xmlns.

#### ArrayGraphTools

Zoom and pan toolbar rendered next to the graph.

```xml
<ArrayGraphTools
    BackgroundColor="[SMSolidColorBrush]#fff7f7f7"
    Graph="[UIModel]<graph-id>"
    Height="[float]26"
    Id="<32-char-hex>"
    Left="[float]10"
    OffsetX="[float]346"
    OffsetY="[float]0"
    Top="[float]30"
    Width="[float]122">
  <!-- ComposableButton children are generated automatically; do not hand-author -->
</ArrayGraphTools>
```

`OffsetX` / `OffsetY` position the toolbar relative to the graph's plot area origin.
The `ComposableButton` children (zoom horizontal, zoom vertical, pan) are complex
NI-generated elements — copy them verbatim from a generator output rather than
hand-authoring.

#### HmiChartPlotLegend

Series legend (lists series names and colors).

```xml
<HmiChartPlotLegend
    Graph="[UIModel]<graph-id>"
    Height="[float]28"
    Id="<32-char-hex>"
    Left="[float]10"
    Top="[float]30"
    Visible="[bool]True" />
```

Optional attribute: `LegendHeightFollowsGraph="[bool]False"`.

#### HmiChartCursorLegend

Cursor readout legend (shows X/Y values at cursor positions).

```xml
<HmiChartCursorLegend
    Graph="[UIModel]<graph-id>"
    Height="[float]80"
    Id="<32-char-hex>"
    Left="[float]10"
    MinHeight="[float]80"
    Top="[float]30"
    Visible="[bool]False"
    Width="[float]316" />
```

Usually hidden by default (`Visible="[bool]False"`) in NI samples.

#### HmiChartScaleLegend

Axis scale legend.

```xml
<HmiChartScaleLegend
    Graph="[UIModel]<graph-id>"
    Height="[float]52"
    Id="<32-char-hex>"
    Left="[float]10"
    Top="[float]30"
    Visible="[bool]False" />
```

Usually hidden by default in NI samples.

---

## 4. Channel binding

Every data control has a `Channel` attribute that links it to a measurement parameter:

```
[string]{<service-uuid>}/Configuration/<DisplayName>   ← input parameter
[string]{<service-uuid>}/Output/<DisplayName>           ← output value
```

- `<service-uuid>` is the value of the `ClientId` attribute on the `Screen` element **in the
  same `.measui` file** (format: `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`). The generator
  assigns this UUID at file creation time. It does **not** appear in `.serviceconfig` — the
  service connection is made via `Screen ServiceClass`, not via this UUID. Every `Channel`
  binding in a single `.measui` file must use the same UUID.
- `<DisplayName>` must **exactly** match the string passed to
  `@measurement_service.configuration("DisplayName", ...)` or
  `@measurement_service.output("DisplayName", ...)` in `measurement.py`, including spaces
  and capitalisation.

---

## 5. ID format rules

Element `Id` attributes and `[UIModel]<id>` cross-references use **lowercase hexadecimal
strings with no dashes**. Most are 32 characters, but NI-published samples contain IDs of
30 and 31 characters that parse correctly (11 of 12 samples contain at least one shorter ID).
When hand-authoring, 32 characters is the safest choice:

```
a1000001000000000000000000000001        VALID (32 chars — recommended for hand-authoring)
72b5606765b48f6a03e01d0505d78c9         VALID (31 chars — present in NI samples)
a1000001-0000-0000-0000-000000000001    INVALID (dashes not allowed in element Id)
```

**Exception — `Screen ClientId`:** this one attribute uses the UUID brace format
`{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}` with dashes. All other `Id` attributes use the
dash-free hex format above.

Every element must have a globally unique ID within the file. Cross-references use
`[UIModel]<id>` as the attribute value:

```xml
<ChannelNumericText ... Label="[UIModel]b1000003000000000000000000000003" ... />
<Label ... Id="b1000003000000000000000000000003" LabelOwner="[UIModel]b1000002000000000000000000000002" ... />
```

---

## 6. Attribute value type syntax

NI SFP XML uses typed attribute values with bracket prefixes:

### 6.1 Primitive types

| Type prefix | Syntax example | Notes |
|---|---|---|
| `[float]` | `[float]24` | Used for most numeric attributes (Left, Top, Width, Height, etc.) |
| `[double]` | `[double]1` | Used for `LineThickness` in `HmiGraphPlot` `PlotRenderer` |
| `[int]` | `[int]1` | Integer attributes (Rows, Columns, TabIndex, Value, etc.) |
| `[uint]` | `[uint]1` | Alternate integer form; seen on `Interval` in some samples |
| `[bool]` | `[bool]True` | Boolean attributes; values are `True` or `False` |
| `[string]` | `[string]My Label` | Text content, empty string: `[string]` |

### 6.2 Reference types

| Type prefix | Syntax example | Notes |
|---|---|---|
| `[Type]` | `[Type]Double` | `ValueType` on numeric controls and array viewers. Valid values: `Double`, `Single`, `Int32`, `UInt32`, `UInt64`, `String` |
| `[UIModel]` | `[UIModel]a1000001000000000000000000000001` | Cross-reference to another element's `Id` |
| `[NI_Core_DataValues_TagRefnum]` | `[NI_Core_DataValues_TagRefnum]Pin1` | Default pin name on `ChannelPinSelector` (`SelectedResource`) |

### 6.3 Color types

Colors use ARGB hex: `#aarrggbb` where `aa` = alpha (ff = opaque, 00 = transparent), `rr`/`gg`/`bb` = RGB channels.

| Type prefix | Syntax example | Notes |
|---|---|---|
| `[SMSolidColorBrush]` | `[SMSolidColorBrush]#ffffffff` | Solid color; used on `BackgroundColor`, `LineStroke`, `PointFill`, etc. |
| `[SMColor]` | `[SMColor]#00ffffff` | Used only on `Color` in `GridLines` element |

### 6.4 Layout types

| Type prefix | Syntax example | Notes |
|---|---|---|
| `[SMThickness]` | `[SMThickness]50,26,20,40` | Four values: left,top,right,bottom (no spaces). Used for `PlotAreaMargin` |
| `[IRange]` | `[IRange]0, 10, System.Double` | Axis range: min, max, type (spaces after commas). Always `System.Double` |
| `[ArrayElementIndex]` | `[ArrayElementIndex]0` | First visible index in `ChannelArrayViewer`. 1D: `0`; 2D: `0,0` |

### 6.5 Visibility and orientation

| Type prefix | Values | Used on |
|---|---|---|
| `[SMVisibility]` | `Visible`, `Collapsed` | Most visibility attributes (`LabelVisibility`, `MinorTickVisibility`, etc.) |
| `[Visibility]` | `Collapsed` | `ContentVisibility` (on `ChannelLED`), `IndexVisibility` (on `ChannelArrayViewer`) |
| `[SMOrientation]` | `Horizontal`, `Vertical` | `Orientation` on `ChannelArrayViewer`, `ArrayGraphAxis`, `ChannelSwitch` |
| `[ScrollBarVisibility]` | `Auto`, `Hidden`, `Visible` | `HorizontalScrollBarVisibility`, `VerticalScrollBarVisibility` |

### 6.6 Enum types

Each enum type has a fixed set of valid values:

| Type prefix | Valid values | Used on |
|---|---|---|
| `[RenderMode]` | `Hardware` | `RenderMode` on `ArrayGraph` |
| `[RangeAdjuster]` | `FitExactly` | `Adjuster` on `ArrayGraphAxis` (note: `FitData` is invalid) |
| `[RangeDivisionsMode]` | `Auto` | `Mode` on `RangeLabeledDivisions` |
| `[FillBaseline]` | `Zero` | `AreaBaseline`, `BarBaseline` on `PlotRenderer` |
| `[PointShape]` | `Ellipse`, `Cross`, `Diamond`, `Rectangle` | `PointShape` on `PlotRenderer` |
| `[LEDShape]` | `Round` | `Shape` on `ChannelLED` |
| `[SwitchShape]` | `Slider` | `Shape` on `ChannelSwitch` |
| `[SelectorInteractionModes]` | `ReadOnly` | `InteractionMode` on `ChannelEnumSelector` (read-only output) |
| `[PathSelectorInteractionModes]` | `BrowseDialog, TextInput` | `InteractionMode` on `ChannelPathSelector` |
| `[MultipleSelectionModes]` | `List` | `MultipleSelectionMode` on `ChannelPinSelector` |
| `[RadixBase]` | `0`, `Decimal` | `RadixBase` on `ChannelNumericText` |
| `[SMStretch]` | `Uniform` | `Stretch` on `Image` element (rare) |
| `[TextWrapping]` | `Wrap` | `TextWrapping` on text elements (rare) |

---

## 7. Rules that cause parse errors

These were discovered through trial and error. Violations produce "The source file format
is invalid" with no further detail.

| Rule | Bad example | Fix |
|---|---|---|
| No XML comments | `<!-- comment -->` | Delete the comment |
| Element `Id` must not use UUID dash format (only `Screen ClientId` uses dashes) | `a100001-0000-...` | Use `a1000001000000000000000000000001` (30–32 lowercase hex chars, no dashes) |
| `ValueType="[Type]Boolean"` on ChannelNumericText is not supported | `ValueType="[Type]Boolean"` | Use `[Type]Double` (0.0/1.0) — see section 9 |
| No duplicate attributes on any element | two `IsReadOnly="..."` | Remove the duplicate |
| Every `Label` must have `LabelOwner` | `<Label>` with no `LabelOwner` anywhere | Add `LabelOwner="[UIModel]<target-id>"` pointing to the owning element (control, graph, or canvas). Standalone section-header labels are not supported. |
| Axis adjuster | `Adjuster="[RangeAdjuster]FitData"` | Use `FitExactly` |
| PlotRenderer inside HmiGraphPlot | adding `PointShape` or `AreaBaseline` | Only `Id`, `LineStroke`, `LineThickness`, `PointFill`, `xmlns` |
| PlotRenderer as direct child of ArrayGraph | adding `LineThickness` | Only `AreaBaseline`, `BarBaseline`, `Id`, `PointFill`, `PointShape`, `xmlns` |
| Non-ASCII characters in text | `Text="[string]V → A"` (Unicode right arrow U+2192) | Use ASCII only: `V to A` |

---

## 8. Checksum field

The `Checksum` attribute on `SourceFile` must be present but its algorithm is unknown. Set
it to 128 zeros as a placeholder:

```xml
<SourceFile Checksum="00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000" ...>
```

The NI editor will recompute it when the file is saved through the GUI.

---

## 9. Control type coverage

All standard `DataType` values have a native control element. No workarounds are currently
required:

| DataType | Output (read-only) | Input (writable) |
|---|---|---|
| `Boolean` | `ChannelLED` (section 3.9) | `ChannelCheckBox` (3.10) or `ChannelSwitch` (3.11) |
| `Enum` | `ChannelEnumSelector` with `InteractionMode=ReadOnly` (section 3.8) | `ChannelEnumSelector` (3.8) |
| `Double`, `Int32`, etc. | `ChannelNumericText` with `IsReadOnly` (section 3.3) | `ChannelNumericText` (3.3) |
| `DoubleArray1D`, `Int32Array1D`, etc. | `ChannelArrayViewer` with inner `IsReadOnly` (section 3.4) | `ChannelArrayViewer` (3.4) |
| `String` | `ChannelStringControl` with `IsReadOnly` (section 3.12) | `ChannelStringControl` (3.12) |
| `IOResourceArray1D` (pin names) | — | `ChannelPinSelector` (section 3.5) |
| `Path` | — | `ChannelPathSelector` (section 3.13) |

**Note on `[Type]Boolean`:** `ValueType="[Type]Boolean"` on `ChannelNumericText` causes a
parse error (see section 7). This is not a workaround situation — use `ChannelLED` for
boolean output and `ChannelCheckBox` or `ChannelSwitch` for boolean input.

