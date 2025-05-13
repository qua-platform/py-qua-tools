import pytest
from qualang_tools.config.helper_tools import *
import numpy as np
from scipy.signal.windows import gaussian
from copy import deepcopy


@pytest.fixture
def config0():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                    3: {"offset": 0.0},
                    4: {"offset": 0.0},
                    5: {"offset": 0.0},
                },
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            }
        },
        "elements": {
            "qubit": {
                "mixInputs": {
                    "I": ("con1", 2),
                    "Q": ("con1", 3),
                    "lo_frequency": 0,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 100e6,
                "operations": {},
            },
            "resonator": {
                "mixInputs": {
                    "I": ("con1", 4),
                    "Q": ("con1", 5),
                    "lo_frequency": 0,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 100e6,
                "operations": {"readout": "readout_pulse"},
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": 24,
                "smearing": 0,
            },
            "flux_line": {
                "singleInput": {
                    "single": ("con1", 6),
                },
                "intermediate_frequency": 0e6,
                "operations": {},
            },
        },
        "pulses": {
            "readout_pulse": {
                "operation": "measurement",
                "length": 112,
                "waveforms": {
                    "I": "readout_wf",
                    "Q": "zero_wf",
                },
                "integration_weights": {
                    "cos": "cosine_weights",
                    "sin": "sine_weights",
                    "minus_sin": "minus_sine_weights",
                },
                "digital_marker": "ON",
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
            "readout_wf": {"type": "constant", "sample": 0.2},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "integration_weights": {
            "cosine_weights": {
                "cosine": [(1.0, 80)],
                "sine": [(0.0, 80)],
            },
            "sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(1.0, 80)],
            },
            "minus_sine_weights": {
                "cosine": [(0.0, 80)],
                "sine": [(-1.0, 80)],
            },
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 100e6,
                    "lo_frequency": 0,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
        },
    }


@pytest.fixture
def negative_delay_config():
    return {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0, "delay": -24.0},
                    2: {"offset": 0.0, "delay": -100.0},
                    3: {"offset": 0.0, "delay": 12.0},
                    4: {"offset": 0.0, "delay": 16.0},
                    5: {"offset": 0.0, "delay": 0.0},
                },
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            }
        },
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "digital_waveforms": {},
        "integration_weights": {},
        "mixers": {},
    }


def test_update_integration_weight(config0):
    conf = deepcopy(config0)
    config = QuaConfig(conf)
    # Test update with only one operation using these iw
    config.update_integration_weight("resonator", "readout", "cos", [(1, 180)], [(0, 180)])
    assert conf["integration_weights"]["cosine_weights"]["cosine"][0] == (1, 180)
    assert conf["integration_weights"]["cosine_weights"]["sine"][0] == (0, 180)
    # Add another operation using the same iw
    config.copy_operation("resonator", "readout", "short_readout")
    # Test update with two operations using these iw anf force_update=False
    try:
        config.update_integration_weight("resonator", "readout", "cos", [(1, 80)], [(0, 80)])
    except Exception as e:
        assert (
            e.__str__()
            == "The updated integration weights are used in other operations. To force the update, please set the force_update flag to True."
        )
        assert conf["integration_weights"]["cosine_weights"]["cosine"][0] == (1, 180)
    # Test update with two operations using these iw anf force_update=True
    config.update_integration_weight("resonator", "readout", "cos", [(1, 80)], [(0, 80)], True)
    assert conf["integration_weights"]["cosine_weights"]["cosine"][0] == (1, 80)
    assert conf["integration_weights"]["cosine_weights"]["sine"][0] == (0, 80)


def test_add_control_operation_iq(config0):
    conf = deepcopy(config0)
    config = QuaConfig(conf)

    config.add_control_operation_iq("qubit", "gate", list(gaussian(112, 20)), [0.0 for _ in range(112)])
    assert "gate" in config["elements"]["qubit"]["operations"]
    assert "qubit_gate_pulse" in conf["pulses"]
    assert "qubit_gate_wf_i" in conf["waveforms"]
    assert conf["waveforms"]["qubit_gate_wf_i"]["samples"] == list(gaussian(112, 20))


def test_update_op_amp(config0):
    conf = deepcopy(config0)
    config = QuaConfig(conf)

    config.add_control_operation_single("flux_line", "bias", [0.1 for _ in range(112)])
    assert config["waveforms"]["flux_line_bias_single_wf"]["sample"] == 0.1
    config.update_op_amp("flux_line", "bias", 0.25)
    assert config["waveforms"]["flux_line_bias_single_wf"]["sample"] == 0.25


def test_update_update_waveforms(config0):
    conf = deepcopy(config0)
    config = QuaConfig(conf)

    config.update_waveforms("resonator", "readout", ([1.1] * 175, [0.5] * 175))
    assert config["pulses"]["readout_pulse"]["length"] == 175
    assert config["waveforms"]["resonator_readout_wf_i"]["sample"] == 1.1
    assert config["waveforms"]["resonator_readout_wf_q"]["sample"] == 0.5
    config.add_control_operation_single("flux_line", "bias", [0.1 for _ in range(112)])
    config.update_waveforms("flux_line", "bias", ([1.1] * 175,))
    assert config["waveforms"]["flux_line_bias_single_wf"]["sample"] == 1.1
    assert config["pulses"]["flux_line_bias_pulse"]["length"] == 175
    config.update_waveforms("flux_line", "bias", (list(gaussian(112, 20)),))
    assert config["waveforms"]["flux_line_bias_single_wf"]["samples"] == list(gaussian(112, 20))


def test_transform_negative_delays(negative_delay_config):
    initial_config = deepcopy(negative_delay_config)
    corrected_config = {
        "version": 1,
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0, "delay": 76.0},
                    2: {"offset": 0.0, "delay": 0.0},
                    3: {"offset": 0.0, "delay": 112.0},
                    4: {"offset": 0.0, "delay": 116.0},
                    5: {"offset": 0.0, "delay": 100.0},
                },
                "digital_outputs": {},
                "analog_inputs": {
                    1: {"offset": 0.0, "gain_db": 0},  # I from down-conversion
                    2: {"offset": 0.0, "gain_db": 0},  # Q from down-conversion
                },
            }
        },
        "elements": {},
        "pulses": {},
        "waveforms": {},
        "digital_waveforms": {},
        "integration_weights": {},
        "mixers": {},
    }

    test_config = transform_negative_delays(negative_delay_config, create_new_config=True)
    # Test that initial config has not been changed
    assert initial_config == negative_delay_config
    # Test that the updated config is correct
    assert test_config == corrected_config
    # Test that the updated config is correct with create_new_config=False
    transform_negative_delays(negative_delay_config)
    assert test_config == negative_delay_config


@pytest.mark.parametrize(
    "freq, expected_output",
    list(
        zip(
            [
                OPX1000_MW_BANDS[2][1] - 50e6,
                OPX1000_MW_BANDS[2][1] - 600e6,
                OPX1000_MW_BANDS[2][0] - 50e6,
                OPX1000_MW_BANDS[2][0] + 600e6,
            ],
            [3, 2, 1, 2],
        )
    ),
)
def test_get_band(freq, expected_output):
    result = get_band(freq)
    assert result == expected_output


@pytest.mark.parametrize("freq", [OPX1000_MW_BANDS[1][0] - 5e6, OPX1000_MW_BANDS[3][1] + 5e6])
def test_get_band_error(freq):
    with pytest.raises(
        Exception,
        match=f"The specified frequency {freq} Hz is outside of the MW fem bandwidth",
    ):
        get_band(freq)


@pytest.mark.parametrize(
    "desired_power, max_amplitude, expected_output",
    list(
        zip(
            [0, -60, OPX1000_MW_POWER_MAX, 0],
            [1, 1, 1, 0.5],
            [
                (4, 0.6309573444801932),
                (OPX1000_MW_POWER_MIN, 0.0035481338923357532),
                (OPX1000_MW_POWER_MAX, 1.0),
                (10, 0.31622776601683794),
            ],
        )
    ),
)
def test_get_full_scale_power_dBm_and_amplitude(desired_power, max_amplitude, expected_output):
    result = get_full_scale_power_dBm_and_amplitude(desired_power, max_amplitude)
    assert result == expected_output


@pytest.mark.parametrize("desired_power, max_amplitude", list(zip([OPX1000_MW_POWER_MAX], [0.9])))
def test_get_full_scale_power_dBm_and_amplitude_error(desired_power, max_amplitude):
    with pytest.raises(
        Exception,
        match="The desired power is outside the specifications",
    ):
        get_full_scale_power_dBm_and_amplitude(desired_power, max_amplitude)


@pytest.mark.parametrize(
    "desired_power, max_amplitude, expected_output",
    list(
        zip(
            [0, -60, 10, 0],
            [0.125, 1.25, 0.125, 0.5],
            [
                (8.5, 0.11885022274370186),
                (OCTAVE_GAIN_MIN, 0.0031622776601683794),
                (18.5, 0.11885022274370186),
                (-3.5, 0.47315125896148047),
            ],
        )
    ),
)
def test_get_octave_gain_and_amplitude(desired_power, max_amplitude, expected_output):
    result = get_octave_gain_and_amplitude(desired_power, max_amplitude)
    assert result == expected_output


@pytest.mark.parametrize("desired_power, max_amplitude", list(zip([OCTAVE_GAIN_MAX], [0.1])))
def test_get_octave_gain_and_amplitude_error(desired_power, max_amplitude):
    with pytest.raises(
        Exception,
        match="The desired power is outside the specifications",
    ):
        get_octave_gain_and_amplitude(desired_power, max_amplitude)
