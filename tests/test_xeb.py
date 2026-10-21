from copy import deepcopy

import numpy as np

from qualang_tools.bakery.bakery import Baking
from qualang_tools.bakery.xeb import XEB, XEBOpsSingleQubit


def bakery_config():
    def IQ_imbalance(g, phi):
        c = np.cos(phi)
        s = np.sin(phi)
        N = 1 / ((1 - g**2) * (2 * c**2 - 1))
        return [float(N * x) for x in [(1 - g) * c, (1 + g) * s, (1 - g) * s, (1 + g) * c]]

    return {
        "controllers": {
            "con1": {
                "type": "opx1",
                "analog_outputs": {1: {"offset": +0.0}, 2: {"offset": +0.0}, 3: {"offset": +0.0}},
                "digital_outputs": {1: {}, 2: {}},
            }
        },
        "elements": {
            "qe1": {
                "singleInput": {"port": ("con1", 1)},
                "intermediate_frequency": 0,
                "operations": {"playOp": "constPulse"},
            },
            "qe2": {
                "mixInputs": {
                    "I": ("con1", 2),
                    "Q": ("con1", 3),
                    "lo_frequency": 0,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 0,
                "operations": {"constOp": "constPulse_mix"},
            },
        },
        "pulses": {
            "constPulse": {"operation": "control", "length": 1000, "waveforms": {"single": "const_wf"}},
            "constPulse_mix": {"operation": "control", "length": 80, "waveforms": {"I": "const_wf", "Q": "zero_wf"}},
        },
        "waveforms": {
            "zero_wf": {"type": "constant", "sample": 0.0},
            "const_wf": {"type": "constant", "sample": 0.2},
        },
        "mixers": {
            "mixer_qubit": [
                {"intermediate_frequency": 0, "lo_frequency": 0, "correction": IQ_imbalance(0.0, 0.0)},
            ],
        },
    }


def dummy_play(baker: Baking):
    baker.play("playOp", "qe1")


def dummy_align(baker: Baking):
    baker.align("qe1", "qe2")


def test_xeb_builds_sequence():
    ops = XEBOpsSingleQubit(id=dummy_play, sx=dummy_play, sy=dummy_play, sw=dummy_play)
    m_max = 3
    xeb = XEB(deepcopy(bakery_config()), m_max, ops, ops, dummy_play, dummy_align)

    assert xeb.m_max == m_max
    assert len(xeb.operations_list["q1"]) == m_max
    assert len(xeb.operations_list["q2"]) == m_max
    assert len(xeb.duration_tracker) == m_max
    assert xeb.duration_tracker == sorted(xeb.duration_tracker)
    assert xeb.baked_sequence is not None
