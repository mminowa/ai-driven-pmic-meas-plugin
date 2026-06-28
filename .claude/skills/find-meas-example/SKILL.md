---
name: find-meas-example
description: Find verified NI Measurement Plug-In examples that use a given .measui UI control or DataType. Use this BEFORE writing or editing a .measui file — look up the real, working sample and copy from it instead of guessing. Triggers on tasks involving .measui authoring and Measurement Plug-In UI controls (ChannelEnumSelector, ChannelLED, ChannelArrayViewer, ArrayGraph, HmiGraphPlot, etc.).
---

# find-meas-example

The 12 plug-ins under `src/examples/meas-plugin/` are **verified, working NI samples**.
They are the source of truth for *how to write* a `.measui` control. For per-control XML
blocks (full element structures like `ArrayGraph` or `ChannelEnumSelector`), copy from a
verified sample rather than authoring from memory.

## When to use

- Before adding or editing any control in a `.measui` file.
- When you need the correct UI control for a given data type (the type ↔ control pairing).

For `DataType` selection in `measurement.py`, use the **measurement-plugin-sdk** skill instead.

## How to use

Run the lookup script with a search term:

```bash
.claude/skills/find-meas-example/find_example.sh <term>
```

`<term>` is either:
- a **DataType** name (e.g. `Enum`, `DoubleXYData`, `DoubleArray1D`, `IOResource`, `Path`) —
  returns the `measurement.py` lines that use it **and** the `.measui` file(s) of those same
  plug-ins (the UI counterpart to copy from), or
- a **`.measui` control/element tag** (e.g. `ChannelEnumSelector`, `ChannelLED`,
  `ChannelArrayViewer`, `ArrayGraph`, `HmiGraphPlot`) — returns the `.measui` lines using it.

Run with no argument to list every `DataType` that appears in the examples.

Then **Read the returned file:line** and copy the real block — that is the authoritative
pattern. The script only points you to the truth; it does not transcribe it (so it never
goes stale).

## Natural-language → search-token hints

The `.measui` format is XML; translate intent into the actual tag/type before searching:

| You want… | Search term |
|---|---|
| dropdown / enum selector | `Enum` (type) or `ChannelEnumSelector` (control) |
| boolean indicator / lamp | `ChannelLED` |
| boolean input / toggle | `ChannelCheckBox` or `ChannelSwitch` |
| array of numbers (table) | `DoubleArray1D` or `ChannelArrayViewer` |
| an X–Y plot / graph | `DoubleXYData` or `ArrayGraph` / `HmiGraphPlot` |
| pin / channel picker | `IOResource` or `ChannelPinSelector` |
| file path picker | `Path` or `ChannelPathSelector` |
| single number field | `Double` or `ChannelNumericText` |

## Important: examples teach only positive patterns

Samples show what *works*. They cannot tell you what *breaks the parser* (a sample simply
never contains a forbidden construct). For those empirical, failure-derived constraints,
see the **measui-gotchas** skill, and validate a finished `.measui` with
`.claude/skills/measui-gotchas/validate_measui.py`. These are complementary to this skill, not a substitute.
