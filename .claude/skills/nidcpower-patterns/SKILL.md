---
name: nidcpower-patterns
description: nidcpower driver patterns that are non-obvious or differ from standalone examples. Covers initiate() lifecycle, Sense enum mapping, reset() safety, channel list conventions, and simulation values. Use when writing measurement.py or Layer 2 tests that directly create nidcpower sessions.
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
    stack.enter_context(source_ch.initiate())
    stack.enter_context(load_ch.initiate())
    stack.callback(source_ch.reset)   # registered after initiate(), so runs before abort() (LIFO)
    stack.callback(load_ch.reset)
    # ... sweep and measure ...

# Plain call — for Power On DUT (outputs must survive function return)
source_ch.initiate()
load_ch.initiate()
source_ch.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE)
load_ch.wait_for_event(nidcpower.enums.Event.SOURCE_COMPLETE)
yield (True, ...)   # DUT still powered; no abort yet
```

After `channels.reset()`, the session is Uncommitted. Calling `abort()` on an
Uncommitted session is a no-op — safe when ExitStack exits after an explicit reset.

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
    "source_sense", nims.DataType.Enum, SenseMode.LOCAL, enum_type=SenseMode
)

# When setting the driver property:
channels.sense = _SENSE_MAP[source_sense]
```

The same wrapper pattern applies to any nidcpower enum whose values do not start at 0
(e.g. `OutputFunction`, `SourceMode` — though these are typically not exposed as
configuration parameters).

---

## `OutputFunction` — driver values for reference

```python
nidcpower.OutputFunction.DC_VOLTAGE   # value = 1006  — source pin (PPS / SMU)
nidcpower.OutputFunction.DC_CURRENT   # value = 1007  — load pin (electronic load)
```

Always set `output_function` **before** setting level/limit properties, as changing
the function resets level and limit to driver defaults.

---

## Property configuration order

For DC voltage source sessions, set properties in this order to avoid constraint errors:

```python
channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
channels.output_function = nidcpower.OutputFunction.DC_VOLTAGE
channels.voltage_level_range = vin_voltage_level_range
channels.voltage_level = source_initial_voltage
channels.current_limit = vin_current_limit
channels.current_limit_range = vin_current_limit_range
channels.source_delay = hightime.timedelta(seconds=source_delay)
channels.aperture_time = aperture_time
channels.sense = _SENSE_MAP[source_sense]
```

For DC current load sessions:

```python
channels.source_mode = nidcpower.SourceMode.SINGLE_POINT
channels.output_function = nidcpower.OutputFunction.DC_CURRENT
channels.current_level = load_initial_current
channels.voltage_limit_range = iout_voltage_limit_range
channels.source_delay = hightime.timedelta(seconds=source_delay)
channels.aperture_time = aperture_time
channels.sense = _SENSE_MAP[load_sense]
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
source_session.reset()   # safe even if never initiated
load_session.reset()
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
with nidcpower.Session("PXI1Slot2/0", options=_SOURCE_OPTIONS) as session:
    channels = session.channels["0"]
```

---

## Simulation options for Layer 2 tests

Verified simulation option dictionaries for common instruments:

```python
# NI PXIe-4151 (PPS) — input power source
_SOURCE_OPTIONS = {
    "simulate": True,
    "driver_setup": {"Model": "4151", "BoardType": "PXIe"},
}

# NI PXIe-4051 (Electronic Load) — output load
_LOAD_OPTIONS = {
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
