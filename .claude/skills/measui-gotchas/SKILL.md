---
name: measui-gotchas
description: Empirically observed .measui parser failures — constructs that break the NI Measurement Plug-In UI Editor. Use when editing .measui XML to avoid parser errors.
---

# measui-gotchas

> **Status: observed failures, not guesses.**
> Every item below was reproduced: the construct caused the NI Measurement Plug-In UI
> Editor to reject the file with *"The source file format is invalid"* (or an equivalent
> load error). These are **negative constraints** — things that break the parser.
>
> Important: these **cannot be learned from the sample files** under
> `src/examples/meas-plugin/`. A working sample simply never contains a forbidden
> construct, so its absence proves nothing.

For the **positive** side — which control/XML to use for a given data type — use the
**find-meas-example** skill and copy from the real sample.

---

## Constraints (each one observed to break loading)

- **XML comments (`<!-- -->`) are rejected.** Delete all comments from the `.measui`.
- **Non-ASCII characters in attribute text values are rejected.** Use ASCII only.
- **Duplicate attributes on the same element are rejected.** Each attribute name once per tag.
- **Element `Id` must be 30–32 lowercase hex characters, no dashes**
  (e.g. `a1000001000000000000000000000001`).
  - Exception: `Screen ClientId` uses brace-UUID format `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`.
- **A `Label` without a `LabelOwner` is rejected.** Standalone section-header labels placed
  directly in `ScreenSurfaceCanvas` cause a parse error.
- **`ValueType="[Type]Boolean"` on `ChannelNumericText` is rejected.** Use `ChannelLED`
  (output) or `ChannelCheckBox` / `ChannelSwitch` (input) for booleans instead.
- **`Adjuster="[RangeAdjuster]FitData"` is rejected.** Use `FitExactly` for graph axes.
- **Outer `PlotRenderer`** (direct child of `ArrayGraph`): only `AreaBaseline`, `BarBaseline`,
  `Id`, `PointFill`, `PointShape`, `xmlns` are allowed. Adding `LineThickness` / `LineStroke`
  breaks loading.
- **Inner `PlotRenderer`** (inside `HmiGraphPlot`): only `Id`, `LineStroke`, `LineThickness`,
  `PointFill`, `xmlns` are allowed. Adding `PointShape` / `AreaBaseline` / `BarBaseline`
  breaks loading.

---

## Mechanical check

`.claude/skills/measui-gotchas/validate_measui.py <file.measui>` flags the mechanically detectable subset of the
above (comments, non-ASCII, duplicate attributes, bad `Id` format, `FitData`,
`[Type]Boolean`). It is a Linux-runnable lint, **not** a substitute for opening the file in
the Windows UI Editor — only the editor confirms the file truly loads.
