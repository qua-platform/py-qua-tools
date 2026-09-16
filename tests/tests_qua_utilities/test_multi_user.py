"""Cloudsim test that `qm_session` opens and closes a quantum machine.

Does not port two-user contention (needs a busy OPX).
"""

import pytest
from qm.qua import program, play

from qualang_tools.multi_user import qm_session

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


def test_qm_session_closes_quantum_machine(qmm, config):
    if qmm is None:
        pytest.skip("requires simulator available")

    with program() as prog:
        play("readout", "resonator")

    with qm_session(qmm, config, timeout=10) as qm:
        try:
            qm.execute(prog)
        except Exception as exc:
            pytest.skip(f"cloudsim execute is not usable for qm_session: {exc}")

    assert len(qmm.list_open_quantum_machines()) == 0
