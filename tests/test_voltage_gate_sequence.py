from copy import deepcopy

from qualang_tools.voltage_gates import VoltageGateSequence


def sticky_config():
    return {
        "controllers": {
            "con1": {
                "analog_outputs": {
                    1: {"offset": 0.0},
                    2: {"offset": 0.0},
                },
            },
        },
        "elements": {
            "P1_sticky": {
                "singleInput": {"port": ("con1", 1)},
                "sticky": {"analog": True, "duration": 4},
                "operations": {},
            },
            "P2_sticky": {
                "singleInput": {"port": ("con1", 2)},
                "sticky": {"analog": True, "duration": 4},
                "operations": {},
            },
        },
        "pulses": {},
        "waveforms": {},
    }


def test_add_points_registers_voltage_levels():
    config = sticky_config()
    seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])
    seq.add_points("idle", [0.1, -0.2], 100)

    assert seq._voltage_points["idle"]["coordinates"] == [0.1, -0.2]
    assert seq._voltage_points["idle"]["duration"] == 100


def test_init_adds_step_operation_to_config():
    config = sticky_config()
    VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])

    assert config["elements"]["P1_sticky"]["operations"]["step"] == "P1_sticky_step_pulse"
    assert config["pulses"]["P1_sticky_step_pulse"]["length"] == 16
    assert config["waveforms"]["P1_sticky_step_wf"]["sample"] == 0.25


def test_add_points_casts_integer_coordinates():
    config = sticky_config()
    seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])
    seq.add_points("zero", [0, 0], 16)

    assert seq._voltage_points["zero"]["coordinates"] == [0.0, 0.0]
    assert all(isinstance(v, float) for v in seq._voltage_points["zero"]["coordinates"])


def test_init_does_not_mutate_unrelated_elements():
    config = sticky_config()
    original = deepcopy(config)
    VoltageGateSequence(config, ["P1_sticky"])

    assert "P2_sticky" in original["elements"]
    assert "step" not in original["elements"]["P2_sticky"]["operations"]
    assert "step" not in config["elements"]["P2_sticky"]["operations"]
