import pytest
import numpy as np

from qualang_tools.config.configuration import *
from qualang_tools.config.components import *
from qualang_tools.config.builder import ConfigBuilder


@pytest.fixture
def config_resonator():
    cont = Controller("con1")
    res = ReadoutResonator(
        "res1",
        outputs=[cont.analog_output(0), cont.analog_output(1)],
        inputs=[cont.analog_input(0), cont.analog_input(1)],
        intermediate_frequency=2e6,
    )
    res.lo_frequency = 4e9
    wfs = [
        ArbitraryWaveform("wf1", np.linspace(0, -0.5, 16).tolist()),
        ArbitraryWaveform("wf2", np.linspace(0, -0.5, 16).tolist()),
    ]

    ro_pulse = MeasurePulse("ro_pulse", wfs, 16)
    ro_pulse.add(
        Weights(ConstantIntegrationWeights("integ_w1_I", cosine=1, sine=0, duration=16))
    )
    ro_pulse.add(
        Weights(
            ConstantIntegrationWeights("integ_w1_Q", cosine=0, sine=-1, duration=16)
        )
    )
    ro_pulse.add(
        Weights(ConstantIntegrationWeights("integ_w2_I", cosine=0, sine=1, duration=16))
    )
    ro_pulse.add(
        Weights(ConstantIntegrationWeights("integ_w2_Q", cosine=1, sine=0, duration=16))
    )

    res.add(Operation(ro_pulse))

    cb = ConfigBuilder()
    cb.add(cont)
    cb.add(res)
    return cb.build()


def test_controller(config_resonator):
    config = config_resonator
    assert config["version"] == 1
    assert "con1" in [*config["controllers"]]
    assert config["controllers"]["con1"]["type"] == "opx1"
    assert [*config["controllers"]["con1"]["analog_outputs"]] == [0, 1]
    assert [*config["controllers"]["con1"]["analog_inputs"]] == [0, 1]
    assert config["controllers"]["con1"]["analog_outputs"][0]["offset"] == 0
    assert config["controllers"]["con1"]["analog_outputs"][1]["offset"] == 0
    assert config["controllers"]["con1"]["analog_inputs"][0]["offset"] == 0
    assert config["controllers"]["con1"]["analog_inputs"][1]["offset"] == 0


def test_element(config_resonator):
    config = config_resonator
    assert "res1" in [*config["elements"]]
    assert config["elements"]["res1"]["time_of_flight"] == 0
    assert config["elements"]["res1"]["smearing"] == 0
    assert config["elements"]["res1"]["intermediate_frequency"] == 2e6
    assert config["elements"]["res1"]["mixInputs"]["lo_frequency"] == 4e9
    assert config["elements"]["res1"]["mixInputs"]["I"] == ("con1", 0)
    assert config["elements"]["res1"]["mixInputs"]["Q"] == ("con1", 1)
    assert "ro_pulse" in [*config["elements"]["res1"]["operations"]]


def test_pulses(config_resonator):
    config = config_resonator
    assert [*config["pulses"]] == ["ro_pulse"]
    assert config["pulses"]["ro_pulse"]["operation"] == "measure"
    assert config["pulses"]["ro_pulse"]["length"] == 16
    assert config["pulses"]["ro_pulse"]["waveforms"]["I"] == "wf1"
    assert config["pulses"]["ro_pulse"]["waveforms"]["Q"] == "wf2"
    assert [*config["pulses"]["ro_pulse"]["integration_weights"]] == [
        "integ_w1_I",
        "integ_w1_Q",
        "integ_w2_I",
        "integ_w2_Q",
    ]


def test_integration_weights(config_resonator):
    config = config_resonator
    assert [*config["integration_weights"]] == [
        "integ_w1_I",
        "integ_w1_Q",
        "integ_w2_I",
        "integ_w2_Q",
    ]
    assert config["integration_weights"]["integ_w1_I"]["cosine"] == [(1, 16)]
    assert config["integration_weights"]["integ_w1_I"]["sine"] == [(0, 16)]
    assert config["integration_weights"]["integ_w1_Q"]["cosine"] == [(0, 16)]
    assert config["integration_weights"]["integ_w1_Q"]["sine"] == [(-1, 16)]
    assert config["integration_weights"]["integ_w2_I"]["cosine"] == [(0, 16)]
    assert config["integration_weights"]["integ_w2_I"]["sine"] == [(1, 16)]
    assert config["integration_weights"]["integ_w2_Q"]["cosine"] == [(1, 16)]
    assert config["integration_weights"]["integ_w2_Q"]["sine"] == [(0, 16)]


@pytest.fixture
def config_transmon():

    cb = ConfigBuilder()
    cont = Controller("con1")
    cb.add(cont)

    wf1 = ConstantWaveform("wf1", 1.0)
    wf2 = ArbitraryWaveform("wf2", np.linspace(0, -0.5, 16).tolist())

    qb1 = Transmon(
        "qb1",
        I=cont.analog_output(0),
        Q=cont.analog_output(1),
        intermediate_frequency=5e6,
    )
    qb1.lo_frequency = 4e9
    qb1.add(Operation(ControlPulse("pi_pulse", [wf1, wf2], 16)))

    cb.add(qb1)

    qb2 = FluxTunableTransmon(
        "qb2",
        I=cont.analog_output(2),
        Q=cont.analog_output(3),
        fl_port=cont.analog_output(4),
        intermediate_frequency=5e6,
    )
    qb2.lo_frequency = 4.5e9
    qb2.add(Operation(ControlPulse("pi_pulse", [wf1, wf2], 16)))
    qb2.add(Operation(ControlPulse("fl_pulse", [wf1], 16)))

    cb.add(qb2)
    qb1.mixer = Mixer(
        "mx1",
        intermediate_frequency=5e6,
        lo_frequency=4e9,
        correction=Matrix2x2([[1.0, 0.0], [1.0, 0.0]]),
    )

    return cb.build()


def test_transmon(config_transmon):
    config = config_transmon
    assert [*config["elements"]] == ["qb1", "qb2", "qb2_flux_line"]
    assert [*config["mixers"]] == ["mx1"]
    assert [*config["waveforms"]] == ["wf1", "wf2"]
    assert config["mixers"]["mx1"] == [{
        "intermediate_frequency": 5e6,
        "lo_frequency": 4e9,
        "correction": [1.0, 0.0, 1.0, 0.0],
    }]
    assert config["elements"]["qb2_flux_line"]["singleInput"]["port"] == ("con1", 4)
    assert [*config["pulses"]] == ["pi_pulse", "fl_pulse"]
