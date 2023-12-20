import os
from copy import deepcopy
from pathlib import Path

import numpy as np
import pytest

from qualang_tools.bakery.bakery import baking
from qualang_tools.bakery.randomized_benchmark_c1 import c1_table, c1_ops


def gauss(amplitude, mu, sigma, length):
    t = np.linspace(-length / 2, length / 2, length)
    gauss_wave = amplitude * np.exp(-((t - mu) ** 2) / (2 * sigma**2))
    return [float(x) for x in gauss_wave]


def abs_path_to(rel_path: str) -> str:
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    return os.path.join(source_dir, rel_path)


@pytest.fixture
def config():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [
            float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]
        ]

    return {
        "version": 1,
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {
                    1: {"offset": +0.0},
                    2: {"offset": +0.0},
                    3: {"offset": +0.0},
                },
                "digital_outputs": {1: {}, 2: {}},
            }
        },
        "elements": {
            "qe1": {
                "singleInput": {"port": ("con1", 1)},
                "intermediate_frequency": 0,
                "operations": {
                    "playOp": "constPulse",
                    "a_pulse": "arb_pulse1",
                    "playOp2": "constPulse2",
                },
                "digitalInputs": {
                    "digital_input1": {
                        "port": ("con1", 1),
                        "delay": 0,
                        "buffer": 0,
                    }
                },
            },
            "qe2": {
                "mixInputs": {
                    "I": ("con1", 2),
                    "Q": ("con1", 3),
                    "lo_frequency": 0,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 0,
                "operations": {"constOp": "constPulse_mix", "gaussOp": "gauss_pulse"},
            },
            "qe3": {
                "RF_inputs": {"port": ("octave1", 1)},
                "intermediate_frequency": 50e6,
                "operations": {"constOp": "constPulse_mix", "gaussOp": "gauss_pulse"},
            },
        },
        "octaves": {
            "octave1": {
                "RF_outputs": {
                    1: {
                        "LO_frequency": 6e9,
                        "LO_source": "internal",
                        "output_mode": "always_on",
                        "gain": 0,
                    },
                },
            },
        },
        "pulses": {
            "constPulse": {
                "operation": "control",
                "length": 1000,  # in ns
                "waveforms": {"single": "const_wf"},
            },
            "constPulse2": {
                "operation": "control",
                "length": 1000,  # in ns
                "waveforms": {"single": "const_wf"},
                "digital_marker": "ON",
            },
            "arb_pulse1": {
                "operation": "control",
                "length": 100,  # in ns
                "waveforms": {"single": "arb_wf"},
            },
            "constPulse_mix": {
                "operation": "control",
                "length": 80,
                "waveforms": {"I": "const_wf", "Q": "zero_wf"},
            },
            "gauss_pulse": {
                "operation": "control",
                "length": 80,
                "waveforms": {"I": "gauss_wf", "Q": "zero_wf"},
            },
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
            "arb_wf": {"type": "arbitrary", "samples": [i / 200 for i in range(100)]},
            "gauss_wf": {"type": "arbitrary", "samples": gauss(0.2, 0, 15, 80)},
        },
        "digital_waveforms": {
            "ON": {"samples": [(1, 0)]},
        },
        "mixers": {
            "mixer_qubit": [
                {
                    "intermediate_frequency": 0,
                    "lo_frequency": 0,
                    "correction": IQ_imbalance(0.0, 0.0),
                }
            ],
        },
    }


def test_c1_data():
    c1_correct_table = np.load(abs_path_to("c1_table.npy"))
    c1_correct_ops = np.load(abs_path_to("c1_ops.npy"), allow_pickle=True)
    assert (c1_correct_table == c1_table).all()
    assert (c1_correct_ops == np.array(c1_ops, dtype=object)).all()


def test_override_waveform(config):
    cfg = deepcopy(config)
    with baking(cfg, padding_method="right", override=True) as b_ref:
        b_ref.play("gaussOp", "qe2")
        b_ref.play("gaussOp", "qe3")
    ref_length = b_ref.get_op_length("qe2")
    ref_length2 = b_ref.get_op_length("qe3")

    with baking(
        cfg,
        padding_method="right",
        override=False,
        baking_index=b_ref.get_baking_index(),
    ) as b_new:
        samples = [[0.2] * 30, [0.0] * 30]
        b_new.add_op("customOp", "qe2", samples)
        b_new.add_op("customOp", "qe3", samples)
        b_new.play("customOp", "qe2")
        b_new.play("customOp", "qe3")

    assert b_new.get_op_length("qe2") == ref_length
    assert b_new.get_op_length("qe3") == ref_length2



def test_out_boolean(config):
    cfg = deepcopy(config)
    with baking(cfg) as b:
        assert not b.is_out()
        b.play("playOp", "qe1")
        assert b.get_current_length("qe1") == 1000
    assert b.is_out()
    with baking(cfg) as b:
        assert b.get_current_length("qe1") == 0
        assert not b.is_out()


def test_delete_Op(config):
    cfg = deepcopy(config)
    with baking(cfg) as b:
        b.play("playOp", "qe1")
        b.play("gaussOp", "qe2")
        b.play("gaussOp", "qe3")
    assert "baked_Op_0" in cfg["elements"]["qe1"]["operations"]
    assert "qe1_baked_pulse_0" in cfg["pulses"]
    assert "qe2_baked_pulse_0" in cfg["pulses"]
    assert "qe3_baked_pulse_0" in cfg["pulses"]
    b.delete_baked_op("qe1")
    assert "baked_Op_0" not in cfg["elements"]["qe1"]["operations"]
    assert "qe1_baked_pulse_0" not in cfg["pulses"]
    with b:
        b.play("playOp", "qe1")
    assert "baked_Op_0" in cfg["elements"]["qe1"]["operations"]
    b.delete_baked_op()
    assert "baked_Op_0" not in cfg["elements"]["qe1"]["operations"]
    assert "baked_Op_0" not in cfg["elements"]["qe2"]["operations"]
    assert "baked_Op_0" not in cfg["elements"]["qe3"]["operations"]

    with baking(cfg) as b:
        b.add_digital_waveform("dig_wf", [(1, 0)])
        b.add_op("new_Op", "qe1", [0.3] * 100, "dig_wf")
        b.play("new_Op", "qe1")

    assert "qe1_baked_digital_wf_0" in cfg["digital_waveforms"]
    b.delete_baked_op()
    assert "qe1_baked_digital_wf_0" not in cfg["digital_waveforms"]


def test_indices_behavior(config):
    cfg = deepcopy(config)
    with baking(cfg) as b1:
        b1.play("gaussOp", "qe2")
        b1.play("gaussOp", "qe3")

    assert all(
        [
            cfg["waveforms"]["qe2_baked_wf_I_0"]["samples"][i]
            == gauss(0.2, 0, 15, 80)[i]
            for i in range(80)
        ]
    )
    assert all(
        [
            cfg["waveforms"]["qe3_baked_wf_I_0"]["samples"][i]
            == gauss(0.2, 0, 15, 80)[i]
            for i in range(80)
        ]
    )
    with b1:
        b1.play("gaussOp", "qe2", amp=2)
        b1.play("gaussOp", "qe3", amp=2)
    assert all(
        [
            cfg["waveforms"]["qe2_baked_wf_I_0"]["samples"][i]
            == gauss(0.4, 0, 15, 80)[i]
            for i in range(80)
        ]
    )
    assert all(
        [
            cfg["waveforms"]["qe3_baked_wf_I_0"]["samples"][i]
            == gauss(0.4, 0, 15, 80)[i]
            for i in range(80)
        ]
    )


def test_play_at_negative_t(config):
    cfg = deepcopy(config)
    with baking(config=cfg, padding_method="symmetric_r") as b:
        const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
        const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.3]
        b.add_op("Op1", "qe2", [const_Op, const_Op2])  # qe1 is a mixInputs element
        b.add_op("Op1", "qe3", [const_Op, const_Op2])  # qe1 is a mixInputs element
        Op3 = [0.1, 0.1, 0.1, 0.1]
        Op4 = [0.1, 0.1, 0.1, 0.1]
        b.add_op("Op2", "qe2", [Op3, Op4])
        b.add_op("Op2", "qe3", [Op3, Op4])
        b.play("Op1", "qe2")
        b.play("Op1", "qe3")
        # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
        #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.3]
        b.play_at(
            "Op2", "qe2", t=-2
        )  # t indicates the time index where these new samples should be added
        b.play_at(
            "Op2", "qe3", t=-2
        )  # t indicates the time index where these new samples should be added
        # The baked waveform is now I: [0.3, 0.3, 0.3, 0.4, 0.4, 0.1, 0.1]
        #                           Q: [0.2, 0.2, 0.2, 0.4, 0.4, 0.1, 0.1]
    assert np.array_equal(
        np.round(np.array(b.get_waveforms_dict()["waveforms"]["qe2_baked_wf_I_0"]), 4),
        np.array([0, 0, 0, 0, 0.3, 0.3, 0.3, 0.4, 0.4, 0.1, 0.1, 0, 0, 0, 0, 0]),
    )
    assert np.array_equal(
        np.round(np.array(b.get_waveforms_dict()["waveforms"]["qe3_baked_wf_I_0"]), 4),
        np.array([0, 0, 0, 0, 0.3, 0.3, 0.3, 0.4, 0.4, 0.1, 0.1, 0, 0, 0, 0, 0]),
    )


def test_negative_wait(config):
    cfg = deepcopy(config)
    with baking(config=cfg, padding_method="symmetric_r") as b:
        const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
        const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.3]
        b.add_op("Op1", "qe2", [const_Op, const_Op2])  # qe1 is a mixInputs element
        b.add_op("Op1", "qe3", [const_Op, const_Op2])  # qe1 is a mixInputs element
        Op3 = [0.1, 0.1, 0.1, 0.1]
        Op4 = [0.1, 0.1, 0.1, 0.1]
        b.add_op("Op2", "qe2", [Op3, Op4])
        b.add_op("Op2", "qe3", [Op3, Op4])
        b.play("Op1", "qe2")
        b.play("Op1", "qe3")
        # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
        #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.3]
        b.wait(-3, "qe2")
        b.wait(-3, "qe3")
        b.play(
            "Op2", "qe2"
        )  # t indicates the time index where these new samples should be added
        b.play(
            "Op2", "qe3"
        )  # t indicates the time index where these new samples should be added
        # The baked waveform is now I: [0.3, 0.3, 0.3, 0.4, 0.4, 0.1, 0.1]
        #                           Q: [0.2, 0.2, 0.2, 0.4, 0.4, 0.1, 0.1]
    assert np.array_equal(
        np.round(np.array(b.get_waveforms_dict()["waveforms"]["qe2_baked_wf_I_0"]), 4),
        np.array([0, 0, 0, 0, 0, 0.3, 0.3, 0.4, 0.4, 0.4, 0.1, 0, 0, 0, 0, 0]),
    )
    assert np.array_equal(
        np.round(np.array(b.get_waveforms_dict()["waveforms"]["qe3_baked_wf_I_0"]), 4),
        np.array([0, 0, 0, 0, 0, 0.3, 0.3, 0.4, 0.4, 0.4, 0.1, 0, 0, 0, 0, 0]),
    )


def test_play_at_negative_t_too_large(config):
    cfg = deepcopy(config)
    with baking(config=cfg, padding_method="symmetric_r") as b:
        const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
        const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.3]
        b.add_op("Op1", "qe2", [const_Op, const_Op2])  # qe1 is a mixInputs element
        b.add_op("Op1", "qe3", [const_Op, const_Op2])  # qe1 is a mixInputs element
        Op3 = [0.1, 0.1, 0.1, 0.1]
        Op4 = [0.1, 0.1, 0.1, 0.1]
        b.add_op("Op2", "qe2", [Op3, Op4])
        b.add_op("Op2", "qe3", [Op3, Op4])
        b.play("Op1", "qe2")
        b.play("Op1", "qe3")
        # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
        #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.3]
        with pytest.raises(
            Exception,
            match="too large for current baked samples length",
        ):
            b.play_at(
                "Op2", "qe2", t=-6
            )  # t indicates the time index where these new samples should be added
            b.play_at(
                "Op2", "qe3", t=-6
            )  # t indicates the time index where these new samples should be added
            # The baked waveform is now I: [0.3, 0.3, 0.3, 0.4, 0.4, 0.1, 0.1]
            #                           Q: [0.2, 0.2, 0.2, 0.4, 0.4, 0.1, 0.1]


def test_negative_wait_too_large(config):
    cfg = deepcopy(config)
    with baking(config=cfg, padding_method="symmetric_r") as b:
        const_Op = [0.3, 0.3, 0.3, 0.3, 0.3]
        const_Op2 = [0.2, 0.2, 0.2, 0.3, 0.3]
        b.add_op("Op1", "qe2", [const_Op, const_Op2])  # qe1 is a mixInputs element
        b.add_op("Op1", "qe3", [const_Op, const_Op2])  # qe1 is a mixInputs element
        Op3 = [0.1, 0.1, 0.1, 0.1]
        Op4 = [0.1, 0.1, 0.1, 0.1]
        b.add_op("Op2", "qe2", [Op3, Op4])
        b.add_op("Op2", "qe3", [Op3, Op4])
        b.play("Op1", "qe2")
        b.play("Op1", "qe3")
        # The baked waveform is at this point I: [0.3, 0.3, 0.3, 0.3, 0.3]
        #                                     Q: [0.2, 0.2, 0.2, 0.3, 0.3]
        with pytest.raises(
            Exception,
            match="too large for current baked samples length",
        ):
            b.wait(-6, "qe2")
            b.wait(-6, "qe3")
            b.play(
                "Op2", "qe2"
            )  # t indicates the time index where these new samples should be added
            b.play(
                "Op2", "qe3"
            )  # t indicates the time index where these new samples should be added
            # The baked waveform is now I: [0.3, 0.3, 0.3, 0.4, 0.4, 0.1, 0.1]
            #                           Q: [0.2, 0.2, 0.2, 0.4, 0.4, 0.1, 0.1]


def test_align_command(config):
    cfg = deepcopy(config)
    with baking(cfg) as b:
        b.play("playOp", "qe1")
        b.play("gaussOp", "qe2")
        b.play("gaussOp", "qe3")
        b.align()

    assert b.get_op_length("qe2") == b.get_op_length("qe1")
    assert b.get_op_length("qe3") == b.get_op_length("qe1")

    with b:
        b.play("playOp", "qe1")
        b.play("gaussOp", "qe2")
        b.play("gaussOp", "qe3")
        b.align("qe1", "qe2")
        b.align("qe1", "qe3")

    assert b.get_op_length("qe2") == b.get_op_length("qe1")
    assert b.get_op_length("qe3") == b.get_op_length("qe1")


def test_add_digital_wf(config):
    cfg = deepcopy(config)
    with baking(cfg) as b:
        b.add_digital_waveform("dig_wf", [(1, 0)])
        b.add_digital_waveform("dig_wf2", [(0, 25), (1, 13), (0, 12)])
        b.add_op("Op2", "qe1", [0.2] * 80, digital_marker="dig_wf2")
        b.add_op("Op", "qe1", [0.1, 0.1, 0.1], digital_marker="dig_wf")
        b.play("Op", "qe1")
        b.play("Op2", "qe1")
    print(cfg["pulses"]["qe1_baked_pulse_0"])
    print(cfg["waveforms"]["qe1_baked_wf_0"])
    print(cfg["digital_waveforms"])
    assert cfg["digital_waveforms"]["qe1_baked_digital_wf_0"]["samples"] == [
        (1, 0),
        (0, 25),
        (1, 13),
        (0, 12),
    ]


def test_constraint_length(config):
    cfg = deepcopy(config)
    with baking(cfg) as b:
        b.add_op("Op", "qe1", [0.2] * 1000)
        b.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
        b.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
        b.play("Op", "qe1")
        b.play("Op2", "qe2")
        b.play("Op2", "qe3")

    assert b.get_op_length() == 1000

    with baking(cfg, baking_index=b.get_baking_index()) as b2:
        b2.add_op("Op", "qe1", [0.2] * 300)
        b2.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
        b2.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
        b2.play("Op", "qe1")
        b2.play("Op2", "qe2")
        b2.play("Op2", "qe3")

    assert b2.get_op_length() == 1000
    assert b2.get_op_length("qe1") == 1000 == b2.get_op_length("qe2")
    assert b2.get_op_length("qe1") == 1000 == b2.get_op_length("qe3")


def test_low_sampling_rate(config):
    cfg = deepcopy(config)
    for i, rate in enumerate([0.1e9, 0.2e9, 0.34e9, 0.4234e9, 0.5e9, 0.788e9]):
        with baking(config, sampling_rate=rate) as b:
            b.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
            b.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
            b.play("Op2", "qe2")
            b.play("Op2", "qe3")

        assert config["waveforms"][f"qe2_baked_wf_I_{i}"]["sampling_rate"] == int(rate)
        assert config["waveforms"][f"qe3_baked_wf_I_{i}"]["sampling_rate"] == int(rate)


def test_high_sampling_rate(config):
    cfg = deepcopy(config)

    for i, rate in enumerate([3e9, 2.546453e9, 8.7654e9, 1.234e9, 2e9, 4e9]):
        with baking(config, sampling_rate=rate, padding_method="symmetric_r") as b:
            b.play("gaussOp", "qe2")
            b.play("gaussOp", "qe3")

            assert b.get_current_length("qe2") == int(np.ceil(rate * 80e-9))
            assert b.get_current_length("qe3") == int(np.ceil(rate * 80e-9))


def test_delete_samples_within_baking(config):
    cfg = deepcopy(config)

    with baking(cfg) as b:
        b.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
        b.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
        b.play("Op2", "qe2")
        b.play("Op2", "qe3")
        b.delete_samples(-100)
        assert b.get_current_length() == 600
        assert b._qe_dict["qe2"]["time"] == 600
        assert b._qe_dict["qe3"]["time"] == 600
    assert b.get_op_length() == 600

    with baking(cfg) as b2:
        b2.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
        b2.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
        b2.play("Op2", "qe2")
        b2.play("Op2", "qe3")
        b2.delete_samples(100)
        assert b2.get_current_length() == 100
        assert b2._qe_dict["qe2"]["time"] == 100
        assert b2._qe_dict["qe3"]["time"] == 100
    assert b2.get_op_length() == 100

    with baking(cfg) as b3:
        b3.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
        b3.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
        b3.play("Op2", "qe2")
        b3.play("Op2", "qe3")
        b3.delete_samples(100, 400)
        assert b3.get_current_length() == 400
        assert b3._qe_dict["qe2"]["time"] == 400
        assert b3._qe_dict["qe3"]["time"] == 400
    assert b3.get_op_length() == 400

    with baking(cfg) as b4:
        b4.add_op("Op2", "qe2", [[0.2] * 700, [0.3] * 700])
        b4.add_op("Op2", "qe3", [[0.2] * 700, [0.3] * 700])
        b4.play("Op2", "qe2")
        b4.play("Op2", "qe3")
        b4.delete_samples(-100, 400)
        assert b4.get_current_length() == 600
        assert b4._qe_dict["qe2"]["time"] == 600
        assert b4._qe_dict["qe3"]["time"] == 600
    assert b4.get_op_length() == 600
