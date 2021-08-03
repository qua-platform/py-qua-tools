# todo
import pytest
from qualang_tools.QuaConfig import QuaConfig

@pytest.fixture
def config():
    pulse_len = 1000
    return QuaConfig(
        {
            "version": 1,
            "controllers": {
                "con1": {
                    "type": "opx1",
                    "analog_outputs": {
                        1: {"offset": +0.0},
                    },
                    "analog_inputs": {
                        1: {"offset": +0.0},
                    },
                }
            },
            "elements": {
                "qe1": {
                    "singleInput": {"port": ("con1", 1)},
                    "outputs": {"output1": ("con1", 1)},
                    "intermediate_frequency": 100e6,
                    "operations": {
                        "readoutOp": "readoutPulse",
                        "readoutOp2": "readoutPulse2",
                    },
                    "time_of_flight": 180,
                    "smearing": 0,
                },
                "qe2": {
                    "mixInputs": {"I": ("con1", 2), "Q": ("con1", 3)},
                    "intermediate_frequency": 100e6,
                    "operations": {
                        "readoutOp": "readoutPulse",
                        "readoutOp2": "readoutPulse2",
                    },
                },
            },
            "pulses": {
                "readoutPulse": {
                    "operation": "measure",
                    "length": pulse_len,
                    "waveforms": {"single": "ramp_wf"},
                    "digital_marker": "ON",
                    "integration_weights": {"x": "xWeights", "y": "yWeights"},
                },
                "readoutPulse2": {
                    "operation": "measure",
                    "length": 2 * pulse_len,
                    "waveforms": {"single": "ramp_wf2"},
                    "digital_marker": "ON",
                    "integration_weights": {"x": "xWeights2", "y": "yWeights"},
                },
            },
            "waveforms": {
                "const_wf": {"type": "constant", "sample": 0.2},
                "ramp_wf": {
                    "type": "arbitrary",
                    "samples": [n / (2 * pulse_len) for n in range(pulse_len)],
                },
                "ramp_wf2": {
                    "type": "arbitrary",
                    "samples": [n / (2 * pulse_len) for n in range(pulse_len)],
                },
            },
            "digital_waveforms": {
                "ON": {"samples": [(1, 0)]},
            },
            "integration_weights": {
                "xWeights": {
                    "cosine": [1.0] * (pulse_len // 4),
                    "sine": [0.0] * (pulse_len // 4),
                },
                "xWeights2": {
                    "cosine": [1.0] * (2 * pulse_len // 4),
                    "sine": [0.0] * (2 * pulse_len // 4),
                },
                "yWeights": {
                    "cosine": [0.0] * (pulse_len // 4),
                    "sine": [1.0] * (pulse_len // 4),
                },
            },
        }
    )


def test_get_port_by_element_input(config):
    # single
    r = config.get_port_by_element_input("qe1", "single")
    assert r == ("con1", 1)
    # IQ pair
    r = config.get_port_by_element_input("qe2", "I")
    assert r == ("con1", 2)


def test_set_output_dc_offset_by_element(config):
    # single
    config.set_output_dc_offset_by_element("qe1", "single", 0.3)
    assert config["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0.3
    # IQ pair
    config.set_output_dc_offset_by_element("qe2", "I", 0.2)
    assert config["controllers"]["con1"]["analog_outputs"][2]["offset"] == 0.2