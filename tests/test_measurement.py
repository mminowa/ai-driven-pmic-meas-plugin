"""Layer 2 — Integration tests using nidcpower simulation.

No real hardware or NI session management service required.
Tests call _run_power_on(), _run_measurement(), and _run_power_off() directly
with simulated nidcpower sessions.

These tests will fail with ImportError until Phase 3 (measurement.py is implemented).

Simulation caveat: simulated sessions do not return realistic voltage/current values.
Tests validate structure and state (array lengths, output_enabled), not numerical accuracy.
"""

import math
import threading

import nidcpower
import pytest

from measurement import _run_measurement, _run_power_off, _run_power_on

# ---------------------------------------------------------------------------
# Simulation options
# ---------------------------------------------------------------------------

_SOURCE_OPTIONS = {
    "simulate": True,
    "driver_setup": {"Model": "4151", "BoardType": "PXIe"},
}
_LOAD_OPTIONS = {
    "simulate": True,
    "driver_setup": {"Model": "4051", "BoardType": "PXIe"},
}

# ---------------------------------------------------------------------------
# Common configuration parameters matching the spec defaults
# (docs/specs/pmic_efficiency.md — Inputs)
# ---------------------------------------------------------------------------

_COMMON_PARAMS: dict = {
    "source_initial_voltage": 1.0,
    "vin_voltage_level_range": 6.0,
    "vin_current_limit": 2.0,
    "vin_current_limit_range": 2.0,
    "source_sense": nidcpower.Sense.LOCAL,
    "load_initial_current": 0.1,
    "iout_voltage_limit_range": 6.0,
    "load_sense": nidcpower.Sense.LOCAL,
    "source_delay": 0.0,   # 0 s for fast simulation runs
    "aperture_time": 0.001,
}

_VIN_LEVELS = [3.3, 5.0]
_IOUT_LEVELS = [0.5, 1.0, 1.5]

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def source_session():
    with nidcpower.Session(resource_name="SimulatedSource", options=_SOURCE_OPTIONS) as session:
        yield session


@pytest.fixture()
def load_session():
    with nidcpower.Session(resource_name="SimulatedLoad", options=_LOAD_OPTIONS) as session:
        yield session


# ---------------------------------------------------------------------------
# 2-1. Power on the DUT
# Test design ref: docs/test-design.md — Layer 2, section 2-1
# ---------------------------------------------------------------------------


class TestRunPowerOn:
    def test_output_enabled_is_true(self, source_session, load_session) -> None:
        result = _run_power_on(source_session, load_session, **_COMMON_PARAMS)
        assert result.output_enabled is True

    def test_array_outputs_are_empty(self, source_session, load_session) -> None:
        result = _run_power_on(source_session, load_session, **_COMMON_PARAMS)
        assert list(result.vin_setpoints) == []
        assert list(result.iout_setpoints) == []


# ---------------------------------------------------------------------------
# 2-2 to 2-6. Perform Measurement
# Test design ref: docs/test-design.md — Layer 2, sections 2-2 through 2-6
# ---------------------------------------------------------------------------


def _consume_measurement_generator(source_session, load_session, **kwargs):
    """Consume the _run_measurement generator and return the final result."""
    result = None
    for result in _run_measurement(source_session, load_session, **kwargs):
        pass
    return result


class TestRunMeasurement:
    @pytest.fixture()
    def result(self, source_session, load_session):
        return _consume_measurement_generator(
            source_session,
            load_session,
            vin_levels=_VIN_LEVELS,
            iout_levels=_IOUT_LEVELS,
            cancellation_event=threading.Event(),
            **_COMMON_PARAMS,
        )

    # 2-2: output lengths
    def test_1d_array_lengths(self, result) -> None:
        expected_len = len(_VIN_LEVELS) * len(_IOUT_LEVELS)
        assert len(result.vin_measurements) == expected_len
        assert len(result.iin_measurements) == expected_len
        assert len(result.vout_measurements) == expected_len
        assert len(result.iout_measurements) == expected_len
        assert len(result.pin_measurements) == expected_len
        assert len(result.pout_measurements) == expected_len
        assert len(result.efficiency_measurements) == expected_len

    def test_efficiency_xy_shape(self, result) -> None:
        assert len(result.efficiency) == len(_VIN_LEVELS)
        for xy in result.efficiency:
            assert len(xy.x_data) == len(_IOUT_LEVELS)
            assert len(xy.y_data) == len(_IOUT_LEVELS)

    def test_setpoint_array_lengths(self, result) -> None:
        assert len(result.vin_setpoints) == len(_VIN_LEVELS)
        assert len(result.iout_setpoints) == len(_IOUT_LEVELS)

    # 2-2: output_enabled is False after measurement
    def test_output_enabled_is_false(self, result) -> None:
        assert result.output_enabled is False

    # 2-3: NaN handling when pin <= 0
    def test_nan_when_pin_not_positive(self, result) -> None:
        n_iout = len(_IOUT_LEVELS)
        for i in range(len(_VIN_LEVELS)):
            for j in range(len(_IOUT_LEVELS)):
                idx = i * n_iout + j
                pin = result.pin_measurements[idx]
                eff = result.efficiency_measurements[idx]
                if pin <= 0.0:
                    assert math.isnan(eff), (
                        f"Expected NaN for pin={pin} at [{i},{j}], got {eff}"
                    )
                else:
                    assert not math.isnan(eff), (
                        f"Unexpected NaN for pin={pin} at [{i},{j}]"
                    )

    # 2-4: sweep order preserved
    def test_sweep_order(self, result) -> None:
        for i, vin in enumerate(_VIN_LEVELS):
            assert result.vin_setpoints[i] == pytest.approx(vin)
        for j, iout in enumerate(_IOUT_LEVELS):
            assert result.iout_setpoints[j] == pytest.approx(iout)

    # 2-7: intermediate yields stream partial results
    def test_intermediate_yields(self, source_session, load_session) -> None:
        yielded = list(
            _run_measurement(
                source_session,
                load_session,
                vin_levels=_VIN_LEVELS,
                iout_levels=_IOUT_LEVELS,
                cancellation_event=threading.Event(),
                **_COMMON_PARAMS,
            )
        )
        total_points = len(_VIN_LEVELS) * len(_IOUT_LEVELS)
        # N_vin * N_iout intermediate yields (output_enabled=True) + 1 final yield
        assert len(yielded) == total_points + 1
        for partial in yielded[:-1]:
            assert partial.output_enabled is True
        assert yielded[-1].output_enabled is False

    # 2-6: cancellation leaves sessions in safe state
    def test_cancellation_results_in_safe_state(
        self, source_session, load_session
    ) -> None:
        cancel_event = threading.Event()
        cancel_event.set()  # pre-set: cancellation is requested before sweep starts
        result = _consume_measurement_generator(
            source_session,
            load_session,
            vin_levels=_VIN_LEVELS,
            iout_levels=_IOUT_LEVELS,
            cancellation_event=cancel_event,
            **_COMMON_PARAMS,
        )
        assert result.output_enabled is False


# ---------------------------------------------------------------------------
# 2-5. Power off the DUT
# Test design ref: docs/test-design.md — Layer 2, section 2-5
# ---------------------------------------------------------------------------


class TestRunPowerOff:
    def test_output_enabled_is_false(self, source_session, load_session) -> None:
        result = _run_power_off(source_session, load_session)
        assert result.output_enabled is False

    def test_array_outputs_are_empty(self, source_session, load_session) -> None:
        result = _run_power_off(source_session, load_session)
        assert list(result.vin_setpoints) == []
        assert list(result.iout_setpoints) == []
