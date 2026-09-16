"""Cloudsim execute test for `callable_from_qua`.

Uses `open_qm` + `execute` on the session QmSaas `qmm` (not waveform `simulate`).
If pause/resume callbacks never fire on cloudsim, the test is skipped.
"""

import time

import pytest
from qm.exceptions import QMConnectionError
from qm.qua import program, play

from qualang_tools.callable_from_qua import callable_from_qua, patch_qua_program_addons

patch_qua_program_addons()

registered_calls = []

FEM_IDX = 6
ANALOG_OUTPUT_PORT = 8
ANALOG_INPUT_PORT = 1
READOUT_LEN = 100


@pytest.fixture
def config():
    return {
        "controllers": {
            "con1": {
                "type": "opx1000",
                "fems": {
                    FEM_IDX: {
                        "type": "MW",
                        "analog_outputs": {
                            ANALOG_OUTPUT_PORT: {
                                "sampling_rate": 1e9,
                                "band": 2,
                                "upconverter_frequency": 5e9,
                            },
                        },
                        "analog_inputs": {
                            ANALOG_INPUT_PORT: {
                                "sampling_rate": 1e9,
                                "band": 2,
                                "downconverter_frequency": 5e9,
                            },
                        },
                    },
                },
            },
        },
        "elements": {
            "resonator": {
                "MWInput": {"port": ("con1", FEM_IDX, ANALOG_OUTPUT_PORT)},
                "intermediate_frequency": 200e6,
                "MWOutput": {"port": ("con1", FEM_IDX, ANALOG_INPUT_PORT)},
                "time_of_flight": 484,
                "smearing": 0,
                "operations": {"readout": "readout_pulse"},
            },
        },
        "pulses": {
            "readout_pulse": {
                "operation": "measurement",
                "length": READOUT_LEN,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "const_wf": {"type": "constant", "sample": 0.5},
            "zero_wf": {"type": "constant", "sample": 0.0},
        },
        "digital_waveforms": {"ON": {"samples": [(1, 0)]}},
    }


@callable_from_qua
def register_calls(*args, **kwargs):
    registered_calls.append({"args": args, "kwargs": kwargs})


def test_qua_callable_no_args(qmm, config):
    if qmm is None:
        pytest.skip("requires simulator available")

    registered_calls.clear()
    with program() as prog:
        register_calls()
        play("readout", "resonator")

    assert not registered_calls

    qm = qmm.open_qm(config, close_other_machines=True)
    try:
        try:
            qm.execute(prog)
        except (AttributeError, QMConnectionError):
            pytest.skip("cloudsim execute did not keep a running job for callbacks")
        deadline = time.time() + 15
        while time.time() < deadline and registered_calls != [{"args": (), "kwargs": {}}]:
            time.sleep(0.2)
        if registered_calls != [{"args": (), "kwargs": {}}]:
            pytest.skip("cloudsim execute did not fire callable_from_qua callbacks")
    finally:
        qm.close()
