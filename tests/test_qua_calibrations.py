import pytest

from qualang_tools.addons.calibration.calibrations import QUA_calibrations


def calibration_config():
    return {
        "controllers": {
            "con1": {
                "analog_outputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}, 3: {"offset": 0.0}, 4: {"offset": 0.0}},
                "analog_inputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}},
            }
        },
        "elements": {
            "resonator": {
                "mixInputs": {"I": ("con1", 1), "Q": ("con1", 2), "lo_frequency": 0, "mixer": "mixer"},
                "operations": {"readout": "readout_pulse"},
                "outputs": {"out1": ("con1", 1), "out2": ("con1", 2)},
                "time_of_flight": 24,
                "smearing": 0,
                "intermediate_frequency": 0,
            },
            "qubit": {
                "mixInputs": {"I": ("con1", 3), "Q": ("con1", 4), "lo_frequency": 0, "mixer": "mixer"},
                "operations": {"pi": "pi_pulse"},
                "intermediate_frequency": 0,
            },
        },
        "pulses": {
            "readout_pulse": {
                "operation": "measurement",
                "length": 80,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
                "integration_weights": {
                    "cos": "cos",
                    "sin": "sin",
                    "minus_sin": "minus_sin",
                },
            },
            "pi_pulse": {
                "operation": "control",
                "length": 80,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
            },
        },
        "waveforms": {
            "const_wf": {"type": "constant", "sample": 0.2},
            "zero_wf": {"type": "constant", "sample": 0.0},
        },
        "integration_weights": {
            "cos": {"cosine": [(1.0, 80)], "sine": [(0.0, 80)]},
            "sin": {"cosine": [(0.0, 80)], "sine": [(1.0, 80)]},
            "minus_sin": {"cosine": [(0.0, 80)], "sine": [(-1.0, 80)]},
        },
        "mixers": {"mixer": [{"intermediate_frequency": 0, "lo_frequency": 0, "correction": [1, 0, 0, 1]}]},
    }


def test_qua_calibrations_constructs():
    cal = QUA_calibrations(
        calibration_config(),
        readout=("resonator", "readout"),
        qubit=("qubit", "pi"),
        integration_weights=("cos", "sin", "minus_sin", "cos"),
        outputs=("out1", "out2"),
    )
    assert cal.readout_elmt == "resonator"
    assert cal.qubit_elmt == "qubit"
    assert cal.calibration_list == []


def test_qua_calibrations_unknown_element():
    with pytest.raises(Exception, match="not in the current config"):
        QUA_calibrations(
            calibration_config(),
            readout=("missing", "readout"),
            qubit=("qubit", "pi"),
        )


def test_qua_calibrations_unknown_scan_variable():
    cal = QUA_calibrations(calibration_config())
    with pytest.raises(Exception, match="not implemented"):
        cal.set_rabi([("phase", [0, 1])], iterations=1)
