"""Layer 1 — Unit tests for pure calculation logic.

No hardware, no NI framework, no network required.
These tests will fail with ImportError until Phase 3 (measurement.py is implemented).
"""

import math

import pytest

from measurement import _calculate_efficiency, _calculate_power


class TestCalculateEfficiency:
    """Tests for _calculate_efficiency(pout, pin) -> float.

    Spec ref: docs/specs/pmic_efficiency.md — Outputs: efficiency
    Test design ref: docs/specs/pmic_efficiency_test_cases.md — Layer 1, sections 1-1 and 1-2
    """

    @pytest.mark.parametrize(
        "pout, pin, expected",
        [
            (4.5, 5.0, 90.0),
            (3.0, 4.0, 75.0),
            (0.0, 5.0, 0.0),
            (5.0, 5.0, 100.0),
        ],
    )
    def test_normal_cases(self, pout: float, pin: float, expected: float) -> None:
        assert _calculate_efficiency(pout=pout, pin=pin) == pytest.approx(expected)

    @pytest.mark.parametrize(
        "pout, pin",
        [
            (1.0, 0.0),
            (1.0, -1.0),
            (0.0, 0.0),
        ],
    )
    def test_nan_when_pin_not_positive(self, pout: float, pin: float) -> None:
        assert math.isnan(_calculate_efficiency(pout=pout, pin=pin))


class TestCalculatePower:
    """Tests for _calculate_power(voltage, current) -> float.

    Spec ref: docs/specs/pmic_efficiency.md — Outputs: pin_measurements, pout_measurements
    Test design ref: docs/specs/pmic_efficiency_test_cases.md — Layer 1, section 1-3
    """

    @pytest.mark.parametrize(
        "voltage, current, expected",
        [
            (5.0, 1.0, 5.0),
            (3.3, 0.5, 1.65),
            (0.0, 1.0, 0.0),
        ],
    )
    def test_normal_cases(self, voltage: float, current: float, expected: float) -> None:
        assert _calculate_power(voltage=voltage, current=current) == pytest.approx(expected)
