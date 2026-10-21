"""Offline tests for the QCoDeS OPX driver.

QuantumMachinesManager is mocked. Stream-processing checks compile real QUA programs,
which is the qm-qua surface that breaks when a new SDK release changes the result-analysis model.
"""

import itertools
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

pytest.importorskip("qcodes")

from qm.qua import FUNCTIONS, declare, fixed, program, save, stream_processing

try:
    from qm.qua import declare_output_stream
except ImportError:  # qm-qua < 1.2.4
    from qm.qua import declare_stream as declare_output_stream

from qualang_tools.external_frameworks.qcodes.opx_driver import OPX

_names = itertools.count()
_READOUT_LEN = 4096


def _stream(*, adc_trace=False):
    if adc_trace:
        return declare_output_stream(adc_trace=True)
    return declare_output_stream()


def _config(readout_len=_READOUT_LEN):
    return {
        "elements": {
            "readout_element": {"operations": {"readout": "readout_pulse"}},
        },
        "pulses": {
            "readout_pulse": {
                "length": readout_len,
                "integration_weights": {"cos": "cosine_weights", "sin": "sine_weights"},
            }
        },
        "integration_weights": {
            "cosine_weights": {"cosine": [(1.0, readout_len)], "sine": [(0.0, readout_len)]},
            "sine_weights": {"cosine": [(0.0, readout_len)], "sine": [(1.0, readout_len)]},
        },
    }


@contextmanager
def open_opx(version_dict=None, version_dict_raises=False, config=None):
    version_dict = version_dict or {"OPX": ["1", "2.4.0"], "qm-qua": "1.2.3"}
    with patch("qualang_tools.external_frameworks.qcodes.opx_driver.QuantumMachinesManager") as qmm_cls:
        qmm = qmm_cls.return_value
        if version_dict_raises:
            qmm.version_dict.side_effect = RuntimeError("version_dict removed")
        else:
            qmm.version_dict.return_value = version_dict
        qmm.version.return_value = version_dict
        qm = MagicMock()
        qm.id = "qm-1"
        qmm.open_qm.return_value = qm
        qmm.list_open_quantum_machines.return_value = ["qm-1"]
        inst = OPX(config or _config(), name=f"opx_test_{next(_names)}", host="127.0.0.1")
    try:
        yield inst
    finally:
        inst.close()


def _program_1d():
    with program() as prog:
        i_val = declare(fixed)
        i_stream = _stream()
        save(i_val, i_stream)
        with stream_processing():
            i_stream.buffer(5).save_all("I")
    return prog


def _program_iq_2d():
    with program() as prog:
        i_val = declare(fixed)
        q_val = declare(fixed)
        i_stream = _stream()
        q_stream = _stream()
        save(i_val, i_stream)
        save(q_val, q_stream)
        with stream_processing():
            i_stream.buffer(4).buffer(3).save_all("I")
            q_stream.buffer(4).buffer(3).save_all("Q")
    return prog


def _program_averaged():
    with program() as prog:
        i_val = declare(fixed)
        i_stream = _stream()
        save(i_val, i_stream)
        with stream_processing():
            i_stream.buffer(4).buffer(3).buffer(10).map(FUNCTIONS.average()).save_all("I")
    return prog


def _program_adc():
    with program() as prog:
        adc_stream = _stream(adc_trace=True)
        with stream_processing():
            adc_stream.input1().save_all("adc")
    return prog


def test_measurement_parameter_1d_buffer_shape():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.set_sweep_parameters("axis1", [0, 1, 2, 3, 4], "V", "Inner")
        inst.qua_program = _program_1d()
        param = inst.get_measurement_parameter()

    assert tuple(param.names) == ("I",)
    assert tuple(param.units) == ("V",)
    assert param.shapes == ((5,),)


def test_measurement_parameter_adds_amplitude_and_phase_for_iq():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.set_sweep_parameters("axis1", [0, 1, 2, 3], "V", "Inner")
        inst.set_sweep_parameters("axis2", [0, 1, 2], "V", "Outer")
        inst.qua_program = _program_iq_2d()
        param = inst.get_measurement_parameter()

    assert tuple(param.names) == ("I", "Q", "R", "Phi")
    assert tuple(param.units) == ("V", "V", "V", "deg")
    assert param.shapes == ((3, 4),) * 4


def test_averaging_buffer_is_not_a_setpoint_axis():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.set_sweep_parameters("axis1", [0, 1, 2, 3], "V", "Inner")
        inst.set_sweep_parameters("axis2", [0, 1, 2], "V", "Outer")
        inst.qua_program = _program_averaged()
        param = inst.get_measurement_parameter()
        buffers = inst.results["buffers"]

    assert buffers == [[3, 4]]
    assert 10 not in buffers[0]
    assert tuple(param.names) == ("I",)
    assert param.shapes == ((3, 4),)


def test_adc_trace_sets_readout_time_axis():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.readout_sampling_rate(1)
        inst.qua_program = _program_adc()
        param = inst.get_measurement_parameter()
        result_types = inst.results["types"]
        axis_label = inst.axis1_axis.label
        axis_unit = inst.axis1_axis.unit
        npoints = inst.axis1_npoints()

    assert tuple(param.names) == ("adc",)
    assert result_types == ["adc"]
    assert param.shapes == ((_READOUT_LEN,),)
    assert axis_label == "Readout time"
    assert axis_unit == "ns"
    assert npoints == _READOUT_LEN


def test_scale_factor_overrides_unit_and_volt_conversion():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.set_sweep_parameters("axis1", [0, 1, 2, 3, 4], "V", "Inner")
        inst.qua_program = _program_1d()
        param = inst.get_measurement_parameter(scale_factor=[("I", 2.5, "pA")])
        assert tuple(param.units) == ("pA",)

        handle = MagicMock()
        handle.fetch.return_value = {"value": np.array([-1.0, -2.0, 0.0, 1.0, 2.0])}
        inst.result_handles = MagicMock()
        inst.result_handles.get.return_value = handle
        inst.counter = 1
        fetched = inst.get_res()

    np.testing.assert_allclose(fetched["I"], np.array([2.5, 5.0, 0.0, -2.5, -5.0]))


def test_scale_factor_rejects_a_short_tuple():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.set_sweep_parameters("axis1", [0, 1, 2, 3, 4], "V", "Inner")
        inst.qua_program = _program_1d()
        with pytest.raises(ValueError, match="scale_factor"):
            inst.get_measurement_parameter(scale_factor=[("I", 2.5)])


def test_get_res_builds_amplitude_and_phase():
    with open_opx() as inst:
        inst.readout_pulse_length(_READOUT_LEN)
        inst.set_sweep_parameters("axis1", [0, 1], "V", "Inner")
        inst.qua_program = _program_iq_1d()
        inst.get_measurement_parameter()

        values = {
            "I": np.array([-3.0, 0.0]),
            "Q": np.array([0.0, 4.0]),
        }

        def _handle(name):
            handle = MagicMock()
            handle.fetch.return_value = {"value": values[name]}
            return handle

        inst.result_handles = MagicMock()
        inst.result_handles.get.side_effect = _handle
        inst.counter = 1
        fetched = inst.get_res()

    # raw is converted as -value * 4096 / readout_length; length == 4096 so the sign flips.
    np.testing.assert_allclose(fetched["I"], np.array([3.0, 0.0]))
    np.testing.assert_allclose(fetched["Q"], np.array([0.0, -4.0]))
    np.testing.assert_allclose(fetched["R"], np.array([3.0, 4.0]))
    np.testing.assert_allclose(fetched["Phi"], np.array([0.0, -90.0]))


def _program_iq_1d():
    with program() as prog:
        i_val = declare(fixed)
        q_val = declare(fixed)
        i_stream = _stream()
        q_stream = _stream()
        save(i_val, i_stream)
        save(q_val, q_stream)
        with stream_processing():
            i_stream.buffer(2).save_all("I")
            q_stream.buffer(2).save_all("Q")
    return prog


def test_set_sweep_parameters_stores_axis_metadata():
    with open_opx() as inst:
        inst.set_sweep_parameters("axis1", [0.0, 0.1, 0.2], "V", "Gate 1")
        inst.set_sweep_parameters("axis2", [5.0], "Hz", "Frequency")

        assert inst.axis1_npoints() == 3
        assert inst.axis1_start() == 0.0
        assert inst.axis1_stop() == 0.2
        assert inst.axis1_step() == pytest.approx(0.1)
        assert inst.axis1_axis.unit == "V"
        assert inst.axis1_axis.label == "Gate 1"
        np.testing.assert_allclose(inst.axis1_axis(), [0.0, 0.1, 0.2])

        assert inst.axis2_npoints() == 1
        assert inst.axis2_step() == 0
        assert inst.axis2_axis.unit == "Hz"
        assert inst.axis2_axis.label == "Frequency"
        np.testing.assert_allclose(inst.axis2_axis(), [5.0])


def test_update_readout_length_rewrites_constant_weights_and_reopens_qm():
    with open_opx() as inst:
        inst.update_qm = MagicMock()
        inst.update_readout_length("readout_element", "readout", 2000)

        assert inst.config["pulses"]["readout_pulse"]["length"] == 2000
        assert inst.config["integration_weights"]["cosine_weights"]["cosine"] == [(1.0, 2000)]
        assert inst.config["integration_weights"]["cosine_weights"]["sine"] == [(0.0, 2000)]
        assert inst.config["integration_weights"]["sine_weights"]["sine"] == [(1.0, 2000)]
        inst.update_qm.assert_called_once()


@pytest.mark.parametrize(
    ("version_dict", "model"),
    [
        ({"OPX": ["1", "2.4.0"], "qm-qua": "1.2.3"}, "OPX"),
        ({"OPX": ["2", "2.4.0"], "qm-qua": "1.2.3"}, "OPX+"),
        ({"OPX": ["3", "2.4.0"], "qm-qua": "1.2.3"}, "OPX1000"),
        ({"QOP": ["3", "2.4.0"], "qm-qua": "1.2.3"}, "OPX1000"),
        ({"server": ["1", "1.0.0"], "client": "0.9.0"}, "OPX"),
    ],
)
def test_connect_message_identifies_opx_model(capsys, version_dict, model):
    with open_opx(version_dict=version_dict) as inst:
        capsys.readouterr()
        inst.connect_message()
        message = capsys.readouterr().out

    assert f"Connected to: Quantum Machines {model} in " in message
    sdk_version = version_dict.get("qm-qua", version_dict.get("client"))
    assert f"SDK Version = {sdk_version}." in message


def test_connect_message_falls_back_to_version_when_version_dict_is_missing(capsys):
    version = {"QOP": ["2", "2.2.0"], "client": "1.1.7"}
    with open_opx(version_dict=version, version_dict_raises=True) as inst:
        capsys.readouterr()
        inst.connect_message()
        message = capsys.readouterr().out

    assert "Connected to: Quantum Machines OPX+ in " in message
    assert "SDK Version = 1.1.7." in message
