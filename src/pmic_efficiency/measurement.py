"""PMIC efficiency test measurement plug-in."""

from __future__ import annotations

import enum
import logging
import pathlib
import sys
import threading
from typing import NamedTuple, Sequence

import click
import hightime
import ni_measurement_plugin_sdk_service as nims
import nidcpower
import numpy as np
from _helpers import configure_logging, verbosity_option

script_or_exe = sys.executable if getattr(sys, "frozen", False) else __file__
service_directory = pathlib.Path(script_or_exe).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "PMICEfficiency.serviceconfig",
    ui_file_paths=[service_directory / "PMICEfficiency.measui"],
)

_SOURCE_COMPLETE_TIMEOUT = 10.0  # extra seconds beyond source_delay


class MeasurementMode(enum.IntEnum):
    POWER_ON_DUT = 0
    PERFORM_MEASUREMENT = 1
    POWER_OFF_DUT = 2


class SenseMode(enum.IntEnum):
    LOCAL = 0
    REMOTE = 1


_SENSE_MAP = {
    SenseMode.LOCAL: nidcpower.Sense.LOCAL,
    SenseMode.REMOTE: nidcpower.Sense.REMOTE,
}


class _ModeResult(NamedTuple):
    output_enabled: bool
    vin_setpoints: list
    iout_setpoints: list
    vin_measurements: np.ndarray
    iin_measurements: np.ndarray
    pin_measurements: np.ndarray
    vout_measurements: np.ndarray
    iout_measurements: np.ndarray
    pout_measurements: np.ndarray
    efficiency: np.ndarray


_EMPTY_2D = np.zeros((0, 0))


def _calculate_efficiency(pout: float, pin: float) -> float:
    if pin <= 0.0:
        return float("nan")
    return (pout / pin) * 100.0


def _calculate_power(voltage: float, current: float) -> float:
    return voltage * current


def _configure_source(
    session: nidcpower.Session,
    source_initial_voltage: float,
    vin_voltage_level_range: float,
    vin_current_limit: float,
    vin_current_limit_range: float,
    source_sense: nidcpower.Sense,
    source_delay: float,
    aperture_time: float,
) -> None:
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.output_function = nidcpower.OutputFunction.DC_VOLTAGE
    session.voltage_level_range = vin_voltage_level_range
    session.current_limit_range = vin_current_limit_range
    session.voltage_level = source_initial_voltage
    session.current_limit = vin_current_limit
    session.source_delay = hightime.timedelta(seconds=source_delay)
    session.aperture_time = aperture_time
    session.sense = source_sense


def _configure_load(
    session: nidcpower.Session,
    load_initial_current: float,
    iout_voltage_limit_range: float,
    load_sense: nidcpower.Sense,
    source_delay: float,
    aperture_time: float,
) -> None:
    session.source_mode = nidcpower.SourceMode.SINGLE_POINT
    session.output_function = nidcpower.OutputFunction.DC_CURRENT
    session.current_level = load_initial_current
    session.voltage_limit_range = iout_voltage_limit_range
    session.source_delay = hightime.timedelta(seconds=source_delay)
    session.aperture_time = aperture_time
    session.sense = load_sense


def _run_power_on(
    source_session: nidcpower.Session,
    load_session: nidcpower.Session,
    *,
    source_initial_voltage: float,
    vin_voltage_level_range: float,
    vin_current_limit: float,
    vin_current_limit_range: float,
    source_sense: nidcpower.Sense,
    load_initial_current: float,
    iout_voltage_limit_range: float,
    load_sense: nidcpower.Sense,
    source_delay: float,
    aperture_time: float,
) -> _ModeResult:
    _configure_source(
        source_session,
        source_initial_voltage,
        vin_voltage_level_range,
        vin_current_limit,
        vin_current_limit_range,
        source_sense,
        source_delay,
        aperture_time,
    )
    _configure_load(
        load_session,
        load_initial_current,
        iout_voltage_limit_range,
        load_sense,
        source_delay,
        aperture_time,
    )
    timeout = source_delay + _SOURCE_COMPLETE_TIMEOUT
    source_session.initiate()
    source_session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
    load_session.initiate()
    load_session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
    return _ModeResult(
        output_enabled=True,
        vin_setpoints=[],
        iout_setpoints=[],
        vin_measurements=_EMPTY_2D,
        iin_measurements=_EMPTY_2D,
        pin_measurements=_EMPTY_2D,
        vout_measurements=_EMPTY_2D,
        iout_measurements=_EMPTY_2D,
        pout_measurements=_EMPTY_2D,
        efficiency=_EMPTY_2D,
    )


def _run_measurement(
    source_session: nidcpower.Session,
    load_session: nidcpower.Session,
    *,
    vin_levels: Sequence[float],
    iout_levels: Sequence[float],
    cancellation_event: threading.Event,
    source_initial_voltage: float,
    vin_voltage_level_range: float,
    vin_current_limit: float,
    vin_current_limit_range: float,
    source_sense: nidcpower.Sense,
    load_initial_current: float,
    iout_voltage_limit_range: float,
    load_sense: nidcpower.Sense,
    source_delay: float,
    aperture_time: float,
) -> _ModeResult:
    n_vin = len(vin_levels)
    n_iout = len(iout_levels)
    vin_meas = np.zeros((n_vin, n_iout))
    iin_meas = np.zeros((n_vin, n_iout))
    vout_meas = np.zeros((n_vin, n_iout))
    iout_meas = np.zeros((n_vin, n_iout))
    pin_meas = np.zeros((n_vin, n_iout))
    pout_meas = np.zeros((n_vin, n_iout))
    eff = np.full((n_vin, n_iout), float("nan"))

    _configure_source(
        source_session,
        source_initial_voltage,
        vin_voltage_level_range,
        vin_current_limit,
        vin_current_limit_range,
        source_sense,
        source_delay,
        aperture_time,
    )
    _configure_load(
        load_session,
        load_initial_current,
        iout_voltage_limit_range,
        load_sense,
        source_delay,
        aperture_time,
    )
    timeout = source_delay + _SOURCE_COMPLETE_TIMEOUT
    try:
        source_session.initiate()
        source_session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)
        load_session.initiate()
        load_session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)

        cancelled = False
        for i, vin in enumerate(vin_levels):
            source_session.abort()
            source_session.voltage_level = vin
            source_session.initiate()
            source_session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)

            for j, iout in enumerate(iout_levels):
                if cancellation_event.is_set():
                    cancelled = True
                    break
                load_session.abort()
                load_session.current_level = iout
                load_session.initiate()
                load_session.wait_for_event(nidcpower.Event.SOURCE_COMPLETE, timeout=timeout)

                src = source_session.measure_multiple()[0]
                lod = load_session.measure_multiple()[0]
                vin_meas[i, j] = src.voltage
                iin_meas[i, j] = src.current
                vout_meas[i, j] = lod.voltage
                iout_meas[i, j] = lod.current
                pin_meas[i, j] = _calculate_power(src.voltage, src.current)
                pout_meas[i, j] = _calculate_power(lod.voltage, lod.current)
                eff[i, j] = _calculate_efficiency(pout_meas[i, j], pin_meas[i, j])

            if cancelled:
                break
    finally:
        source_session.reset()
        load_session.reset()

    return _ModeResult(
        output_enabled=False,
        vin_setpoints=list(vin_levels),
        iout_setpoints=list(iout_levels),
        vin_measurements=vin_meas,
        iin_measurements=iin_meas,
        pin_measurements=pin_meas,
        vout_measurements=vout_meas,
        iout_measurements=iout_meas,
        pout_measurements=pout_meas,
        efficiency=eff,
    )


def _run_power_off(
    source_session: nidcpower.Session,
    load_session: nidcpower.Session,
) -> _ModeResult:
    source_session.reset()
    load_session.reset()
    return _ModeResult(
        output_enabled=False,
        vin_setpoints=[],
        iout_setpoints=[],
        vin_measurements=_EMPTY_2D,
        iin_measurements=_EMPTY_2D,
        pin_measurements=_EMPTY_2D,
        vout_measurements=_EMPTY_2D,
        iout_measurements=_EMPTY_2D,
        pout_measurements=_EMPTY_2D,
        efficiency=_EMPTY_2D,
    )


@measurement_service.register_measurement
@measurement_service.configuration(
    "Measurement Mode",
    nims.DataType.Enum,
    MeasurementMode.POWER_ON_DUT,
    enum_type=MeasurementMode,
)
@measurement_service.configuration(
    "Source Pin",
    nims.DataType.IOResourceArray1D,
    ["VIN"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
@measurement_service.configuration(
    "Load Pin",
    nims.DataType.IOResourceArray1D,
    ["VOUT"],
    instrument_type=nims.session_management.INSTRUMENT_TYPE_NI_DCPOWER,
)
@measurement_service.configuration("Vin Levels (V)", nims.DataType.DoubleArray1D, [3.3, 5.0])
@measurement_service.configuration("Iout Levels (A)", nims.DataType.DoubleArray1D, [0.5, 1.0, 1.5, 2.0])
@measurement_service.configuration("Source Initial Voltage (V)", nims.DataType.Double, 1.0)
@measurement_service.configuration("Vin Voltage Level Range (V)", nims.DataType.Double, 6.0)
@measurement_service.configuration("Vin Current Limit (A)", nims.DataType.Double, 2.0)
@measurement_service.configuration("Vin Current Limit Range (A)", nims.DataType.Double, 2.0)
@measurement_service.configuration(
    "Source Sense",
    nims.DataType.Enum,
    SenseMode.LOCAL,
    enum_type=SenseMode,
)
@measurement_service.configuration("Iout Voltage Limit Range (V)", nims.DataType.Double, 6.0)
@measurement_service.configuration("Load Initial Current (A)", nims.DataType.Double, 0.1)
@measurement_service.configuration(
    "Load Sense",
    nims.DataType.Enum,
    SenseMode.LOCAL,
    enum_type=SenseMode,
)
@measurement_service.configuration("Source Delay (s)", nims.DataType.Double, 0.01)
@measurement_service.configuration("Aperture Time (s)", nims.DataType.Double, 0.01)
@measurement_service.output("Output Enabled", nims.DataType.Boolean)
@measurement_service.output("Vin Setpoints (V)", nims.DataType.DoubleArray1D)
@measurement_service.output("Iout Setpoints (A)", nims.DataType.DoubleArray1D)
@measurement_service.output("Vin Measurements (V)", nims.DataType.Double2DArray)
@measurement_service.output("Iin Measurements (A)", nims.DataType.Double2DArray)
@measurement_service.output("Pin Measurements (W)", nims.DataType.Double2DArray)
@measurement_service.output("Vout Measurements (V)", nims.DataType.Double2DArray)
@measurement_service.output("Iout Measurements (A)", nims.DataType.Double2DArray)
@measurement_service.output("Pout Measurements (W)", nims.DataType.Double2DArray)
@measurement_service.output("Efficiency (pct)", nims.DataType.Double2DArray)
def measure(
    measurement_mode: MeasurementMode,
    source_pin: list[str],
    load_pin: list[str],
    vin_levels: list[float],
    iout_levels: list[float],
    source_initial_voltage: float,
    vin_voltage_level_range: float,
    vin_current_limit: float,
    vin_current_limit_range: float,
    source_sense: SenseMode,
    iout_voltage_limit_range: float,
    load_initial_current: float,
    load_sense: SenseMode,
    source_delay: float,
    aperture_time: float,
) -> tuple:
    """Measure PMIC conversion efficiency across Vin and Iout sweep points."""
    logging.info("Executing measurement: mode=%s", measurement_mode.name)

    cancellation_event = threading.Event()
    measurement_service.context.add_cancel_callback(cancellation_event.set)

    common = dict(
        source_initial_voltage=source_initial_voltage,
        vin_voltage_level_range=vin_voltage_level_range,
        vin_current_limit=vin_current_limit,
        vin_current_limit_range=vin_current_limit_range,
        source_sense=_SENSE_MAP[source_sense],
        load_initial_current=load_initial_current,
        iout_voltage_limit_range=iout_voltage_limit_range,
        load_sense=_SENSE_MAP[load_sense],
        source_delay=source_delay,
        aperture_time=aperture_time,
    )

    with measurement_service.context.reserve_sessions(source_pin + load_pin) as reservation:
        with reservation.initialize_nidcpower_sessions() as session_infos:
            source_session = _find_session(session_infos, source_pin[0])
            load_session = _find_session(session_infos, load_pin[0])

            if measurement_mode == MeasurementMode.POWER_ON_DUT:
                result = _run_power_on(source_session, load_session, **common)
            elif measurement_mode == MeasurementMode.PERFORM_MEASUREMENT:
                result = _run_measurement(
                    source_session,
                    load_session,
                    vin_levels=vin_levels,
                    iout_levels=iout_levels,
                    cancellation_event=cancellation_event,
                    **common,
                )
            else:
                result = _run_power_off(source_session, load_session)

    logging.info("Completed measurement: output_enabled=%s", result.output_enabled)
    return (
        result.output_enabled,
        result.vin_setpoints,
        result.iout_setpoints,
        result.vin_measurements.tolist(),
        result.iin_measurements.tolist(),
        result.pin_measurements.tolist(),
        result.vout_measurements.tolist(),
        result.iout_measurements.tolist(),
        result.pout_measurements.tolist(),
        result.efficiency.tolist(),
    )


def _find_session(
    session_infos: list,
    pin_name: str,
) -> nidcpower.Session:
    for si in session_infos:
        for mapping in si.channel_mappings:
            if mapping.pin_or_relay_name == pin_name:
                return si.session
    raise ValueError(f"Pin '{pin_name}' not found in reserved sessions")


@click.command
@verbosity_option
def main(verbosity: int) -> None:
    """Host the PMICEfficiency measurement service."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()
