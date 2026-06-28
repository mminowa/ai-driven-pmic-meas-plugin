---
name: nidcpower-patterns
description: nidcpower driver patterns that are non-obvious or differ from standalone examples. Covers initiate() lifecycle (session-scoped, one call per session, comma-list for multi-channel), same-session vs. separate-session patterns, pin map ChannelGroup and session grouping, Sense enum mapping, reset() safety, channel list conventions, and simulation values. Use when writing measurement.py or Layer 2 tests that directly create nidcpower sessions.
---

# nidcpower-patterns

Patterns verified against the nidcpower Python driver (nimi-python) and the
NI Measurement Plug-Ins framework. All examples use simulated sessions unless noted.

---

## `initiate()` — context manager vs. plain call

`initiate()` returns a context manager (`_Acquisition`) that calls `abort()` on `__exit__`.

| Usage | abort() effect on outputs | When to use |
|---|---|---|
| `with ch.initiate():` | **Holds current level** (outputs not turned off) | Measure flow; register `stack.callback(ch.reset)` to turn off outputs on exit |
| `ch.initiate()` (no `with`) | N/A — abort() not called | Power On mode; caller keeps DUT powered |

```python
# Context manager form — safe for measure/reset flows
with ExitStack() as stack:
    stack.enter_context(ch_a.initiate())
    stack.enter_context(ch_b.initiate())
    stack.callback(ch_a.reset)   # registered after initiate(), so runs before abort() (LIFO)
    stack.callback(ch_b.reset)
    # ... sweep and measure ...

# Plain call — for Power On DUT (outputs must survive function return)
ch_a.initiate()
ch_b.initiate()
ch_a.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE)
ch_b.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE)
# DUT is now powered; outputs remain active until abort() or reset()
```

The two patterns above require `ch_a` and `ch_b` to be on **different sessions**.
For same-session scenarios see "Same-session: initiate once" below.

After `channels.reset()`, the session is Uncommitted. Calling `abort()` on an
Uncommitted session is a no-op — safe when ExitStack exits after an explicit reset.

---

## `initiate()` — one call per session; channel argument sets scope, not sequence

The NI documentation states that `initiate()` can be called on specific channels:

```python
my_session.channels["0"].initiate()   # initiate with channel 0 in scope
my_session.initiate()                 # initiate with all channels in scope
```

Specifying a channel subset sets which channels are **in scope** for that initiation.
It does NOT mean channels are started one at a time. `initiate()` always transitions
the **entire session** from Committed → Running in a single atomic step. Once Running,
any further `initiate()` call on that session (even via a different channel object)
raises:

```
-1074118652: The session is already running.
```

When `channels["0"].initiate()` is called on a session that also has channel 1,
channel 1 is part of the same Running session. Its output behavior depends on its
`output_enabled` state, but the session-level state transition affects all channels.

**To include multiple channels of the same session, pass them as a comma-separated
list in a single call:**

```python
# Wrong — second call fails because session is already Running
ch_a.initiate()   # session → Running
ch_b.initiate()   # ERROR: session already running

# Correct — both channels included in one atomic transition
session.channels["0,1"].initiate()
# or equivalently
session.initiate()
```

---

## Same-session: initiate once

When two pins are in the **same nidcpower session** (e.g., two channels of a
multi-channel SMU, or instruments grouped by a shared ChannelGroup in the pin map),
`info_a` and `info_b` returned by `initialize_nidcpower_sessions()` are the same
object. Use the session-level `initiate()` and extract pin-specific channels from
`channel_mappings` for individual configuration:

```python
# Both info_a and info_b are the same session_info object
# channel_list covers all pins — do NOT use it directly for per-pin config
channel_a = next(m.channel for m in info_a.channel_mappings
                 if m.pin_or_relay_name == pin_a)
channel_b = next(m.channel for m in info_b.channel_mappings
                 if m.pin_or_relay_name == pin_b)
ch_a = info_a.session.channels[channel_a]
ch_b = info_a.session.channels[channel_b]

# Configure each pin independently using their specific channel objects
_configure_pin_a(ch_a, ...)
_configure_pin_b(ch_b, ...)

# Power On DUT — initiate the session once
info_a.session.initiate()

# Measure/reset flow — initiate once with ExitStack
with ExitStack() as stack:
    stack.enter_context(info_a.session.initiate())
    stack.callback(info_a.session.reset)
    # ... sweep ch_a and ch_b independently ...
```

---

## Pin map ChannelGroup and session grouping

Per the Measurement Plug-Ins documentation:

> **Each ChannelGroup name defines a session.** Using the same group name for multiple
> device/channel combinations adds them to the same session.

This means the ChannelGroup name is the **session boundary**, not just a label.
Any number of instruments/channels that share a ChannelGroup name are merged into
one nidcpower session by the framework.

```xml
<!-- One session created — Instrument1 and Instrument2 merged -->
<NIDCPowerInstrument name="Instrument1" numberOfChannels="1">
    <ChannelGroup name="CommonDCPowerChannelGroup" />
</NIDCPowerInstrument>
<NIDCPowerInstrument name="Instrument2" numberOfChannels="1">
    <ChannelGroup name="CommonDCPowerChannelGroup" />  ← same name → same session
</NIDCPowerInstrument>
```

Consequence: `initialize_nidcpower_sessions()` returns **one** `session_info` whose
`channel_mappings` contains both pins. `info_a` and `info_b` are the same object.
Calling `initiate()` on `ch_a` then `ch_b` fails — see "Same-session: initiate once"
above.

Use **different names** for instruments that need independent sessions:

```xml
<!-- Two sessions created — Instrument1 and Instrument2 independent -->
<NIDCPowerInstrument name="Instrument1" numberOfChannels="1">
    <ChannelGroup name="Instrument1ChannelGroup" />
</NIDCPowerInstrument>
<NIDCPowerInstrument name="Instrument2" numberOfChannels="1">
    <ChannelGroup name="Instrument2ChannelGroup" />
</NIDCPowerInstrument>
```

With separate sessions, `initialize_nidcpower_sessions()` returns two distinct
`session_info` objects and `ch_a.initiate()` / `ch_b.initiate()` can be called
independently.

---

## `Sense` enum — driver values vs. SDK configuration enum

`nidcpower.Sense` uses **hardware-level integer codes**, not 0-based integers:

```python
nidcpower.Sense.LOCAL   # value = 1008
nidcpower.Sense.REMOTE  # value = 1009
```

`DataType.Enum` in the SDK requires at least one member with value `0`. Passing
`nidcpower.Sense` directly as `enum_type=` will raise `ValueError` at startup.

**Solution**: define a thin wrapper enum in `measurement.py` and map it to the driver enum:

```python
import enum
import nidcpower

class SenseMode(enum.IntEnum):
    LOCAL = 0    # maps to nidcpower.Sense.LOCAL
    REMOTE = 1   # maps to nidcpower.Sense.REMOTE

_SENSE_MAP = {
    SenseMode.LOCAL: nidcpower.Sense.LOCAL,
    SenseMode.REMOTE: nidcpower.Sense.REMOTE,
}

# In the decorator:
@measurement_service.configuration(
    "sense", nims.DataType.Enum, SenseMode.LOCAL, enum_type=SenseMode
)

# When setting the driver property:
channels.sense = _SENSE_MAP[sense]
```

The same wrapper pattern applies to any nidcpower enum whose values do not start at 0
(e.g. `OutputFunction`, `SourceMode` — though these are typically not exposed as
configuration parameters).

---

## `OutputFunction` — driver values for reference

```python
nidcpower.OutputFunction.DC_VOLTAGE   # value = 1006  — voltage source (PPS / SMU)
nidcpower.OutputFunction.DC_CURRENT   # value = 1007  — current sink (electronic load)
```

Always set `output_function` **before** setting level/limit properties, as changing
the function resets level and limit to driver defaults.

---

## Property configuration order

For DC voltage source channels, set properties in this order to avoid constraint errors:

```python
channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
channels.voltage_level_range = voltage_level_range
channels.voltage_level = voltage_level
channels.current_limit = current_limit
channels.current_limit_range = current_limit_range
channels.source_delay = hightime.timedelta(seconds=source_delay)
channels.aperture_time = aperture_time
channels.sense = _SENSE_MAP[sense]
```

For DC current sink channels (electronic load):

```python
channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
channels.output_function = nidcpower.OutputFunction.DC_CURRENT
channels.current_level = current_level
channels.voltage_limit_range = voltage_limit_range
channels.source_delay = hightime.timedelta(seconds=source_delay)
channels.aperture_time = aperture_time
channels.sense = _SENSE_MAP[sense]
```

`voltage_limit` is not applicable for electronic loads (`DC_CURRENT`) and should
not be set. Only `voltage_limit_range` is needed.

---

## `source_delay` — must use `hightime.timedelta`

The `source_delay` property accepts a `hightime.timedelta`, not a plain `float`:

```python
import hightime
channels.source_delay = hightime.timedelta(seconds=source_delay)
```

Passing a plain `float` raises `TypeError`.

---

## `reset()` — safe in any state

`session.reset()` is safe to call from any session state (Uncommitted, Committed,
or Running). It is idempotent: calling it twice raises no error.

```python
session_a.reset()   # safe even if never initiated
session_b.reset()
```

Use `reset()` (not `abort()`) for the "Power Off" flow — reset puts the session back
to a known Uncommitted state with safe output levels. `abort()` also transitions to
Uncommitted, but outputs hold their current level and continue providing power.

---

## Channel list in `measurement.py` vs. Layer 2 tests

In `measurement.py`, channel lists come from the framework:

```python
channels = session_info.session.channels[session_info.channel_list]
```

In Layer 2 tests, sessions are created directly. The channel list depends on the
resource name used when opening the session:

| Resource name | `channels[...]` key |
|---|---|
| `"PXI1Slot2"` | `"0"`, `"1"`, … (all channels on the instrument) |
| `"PXI1Slot2/0"` | `"0"` (single channel; instrument opened with `/0`) |

For single-channel simulated sessions in tests, use `"0"`:

```python
with nidcpower.Session("PXI1Slot2/0", options=_PPS_4151_OPTIONS) as session:
    channels = session.channels["0"]
```

---

## Simulation options for Layer 2 tests

Verified simulation option dictionaries for common instruments:

```python
# NI PXIe-4151 (PPS — Programmable Power Supply) — voltage source
_PPS_4151_OPTIONS = {
    "simulate": True,
    "driver_setup": {"Model": "4151", "BoardType": "PXIe"},
}

# NI PXIe-4051 (Electronic Load) — current sink
_ELOAD_4051_OPTIONS = {
    "simulate": True,
    "driver_setup": {"Model": "4051", "BoardType": "PXIe"},
}
```

Use short aperture times and zero source delay in tests to avoid slow waits:

```python
channels.source_delay = hightime.timedelta(seconds=0.0)
channels.aperture_time = 0.001   # 1 ms
```

Simulated sessions return the configured setpoint as the measured voltage/current —
do not assert absolute measurement accuracy in Layer 2 tests.
