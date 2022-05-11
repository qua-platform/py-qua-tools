from tracemalloc import stop
import pytest
import numpy as np

from qualang_tools.config.components import *
from qualang_tools.config.builder import ConfigBuilder
from qualang_tools.config.parameters import Parameter, ConfigVars

from qm.program._qua_config_schema import load_config


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
    try:
        load_config(config)
    except:
        assert False
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
    try:
        load_config(config)
    except:
        assert False
    assert "res1" in [*config["elements"]]
    assert config["elements"]["res1"]["time_of_flight"] == 0
    assert config["elements"]["res1"]["smearing"] == 0
    assert config["elements"]["res1"]["intermediate_frequency"] == 2e6
    assert config["elements"]["res1"]["mixInputs"]["lo_frequency"] == 4e9
    assert config["elements"]["res1"]["mixInputs"]["I"] == ("con1", 0)
    assert config["elements"]["res1"]["mixInputs"]["Q"] == ("con1", 1)
    assert config["elements"]["res1"]["outputs"]["out1"] == ("con1", 0)
    assert config["elements"]["res1"]["outputs"]["out2"] == ("con1", 1)
    assert "ro_pulse" in [*config["elements"]["res1"]["operations"]]


def test_pulses(config_resonator):
    config = config_resonator
    try:
        load_config(config)
    except:
        assert False
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
    try:
        load_config(config)
    except:
        assert False
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
        flux_port=cont.analog_output(4),
        intermediate_frequency=5e6,
    )
    qb2.lo_frequency = 4.5e9
    qb2.add(Operation(ControlPulse("pi_pulse", [wf1, wf2], 16)))
    qb2.add(Operation(ControlPulse("fl_pulse", [wf1], 16)))

    cb.add(qb2)
    qb1.mixer = Mixer(
        "mx1",
        [
            MixerData(
                intermediate_frequency=5e6,
                lo_frequency=4e9,
                correction=Matrix2x2([[1.0, 0.0], [1.0, 0.0]]),
            )
        ],
    )

    return cb.build()


def test_transmon(config_transmon):
    config = config_transmon
    try:
        load_config(config)
    except:
        assert False
    assert [*config["elements"]] == ["qb1", "qb2", "qb2_flux_line"]
    assert [*config["mixers"]] == ["mx1"]
    assert [*config["waveforms"]] == ["wf1", "wf2"]
    assert config["mixers"]["mx1"] == [
        {
            "intermediate_frequency": 5e6,
            "lo_frequency": 4e9,
            "correction": [1.0, 0.0, 1.0, 0.0],
        }
    ]
    assert config["elements"]["qb2_flux_line"]["singleInput"]["port"] == ("con1", 4)
    assert [*config["pulses"]] == ["pi_pulse", "fl_pulse"]


@pytest.fixture
def config_3qb_3res():
    cnot_coupler = ArbitraryWaveform("cnot_coupler", np.random.rand(16))
    rxpio2_I = ArbitraryWaveform("rxpio2_I", np.random.rand(16))
    rxpio2_Q = ArbitraryWaveform("rxpio2_Q", np.random.rand(16))
    cnot_I1 = ArbitraryWaveform("cnot_I1", np.random.rand(16))
    cnot_Q1 = ArbitraryWaveform("cnot_Q1", np.random.rand(16))
    cnot_I2 = ArbitraryWaveform("cnot_I2", np.random.rand(16))
    cnot_Q2 = ArbitraryWaveform("cnot_Q2", np.random.rand(16))

    cb = ConfigBuilder()

    con1 = Controller("con1")
    con2 = Controller("con2")
    con3 = Controller("con3")

    cb.add(con1)
    cb.add(con2)
    cb.add(con3)

    qb1 = Transmon(
        "qb1",
        I=con1.analog_output(1),
        Q=con1.analog_output(2),
        intermediate_frequency=50e6,
    )
    qb1.lo_frequency = 4.8e9

    qb2 = Transmon(
        "qb2",
        I=con2.analog_output(1),
        Q=con2.analog_output(2),
        intermediate_frequency=50e6,
    )
    qb2.lo_frequency = 4.8e9

    qb3 = Transmon(
        "qb3",
        I=con3.analog_output(1),
        Q=con3.analog_output(2),
        intermediate_frequency=50e6,
    )
    qb3.lo_frequency = 4.8e9

    cb.add(qb1)
    cb.add(qb2)
    cb.add(qb3)

    rxpio2_pulse = ControlPulse("rxpio2", [rxpio2_I, rxpio2_Q], 16)
    qb1.add(Operation(rxpio2_pulse))
    qb2.add(Operation(rxpio2_pulse))
    qb3.add(Operation(rxpio2_pulse))

    cc12 = Coupler("cc12", port=con1.analog_output(5))
    cc23 = Coupler("cc23", port=con2.analog_output(5))
    cc31 = Coupler("cc31", port=con3.analog_output(5))

    cb.add(cc12)
    cb.add(cc23)
    cb.add(cc31)

    cnot_coupler_pulse = ControlPulse("cnot_coupler", [cnot_coupler], 16)
    cc12.add(Operation(cnot_coupler_pulse))
    cc23.add(Operation(cnot_coupler_pulse))
    cc31.add(Operation(cnot_coupler_pulse))

    cnot_c_pulse = ControlPulse("cnot_c", [cnot_I1, cnot_Q1], 16)
    cnot_t_pulse = ControlPulse("cnot_t", [cnot_I2, cnot_Q2], 16)

    qb1.add(Operation(cnot_c_pulse, "cnot_12"))
    qb1.add(Operation(cnot_c_pulse, "cnot_13"))
    qb1.add(Operation(cnot_t_pulse, "cnot_21"))
    qb1.add(Operation(cnot_t_pulse, "cnot_31"))

    qb2.add(Operation(cnot_c_pulse, "cnot_21"))
    qb2.add(Operation(cnot_c_pulse, "cnot_23"))
    qb2.add(Operation(cnot_t_pulse, "cnot_12"))
    qb2.add(Operation(cnot_t_pulse, "cnot_32"))

    qb3.add(Operation(cnot_c_pulse, "cnot_31"))
    qb3.add(Operation(cnot_c_pulse, "cnot_32"))
    qb3.add(Operation(cnot_t_pulse, "cnot_13"))
    qb3.add(Operation(cnot_t_pulse, "cnot_23"))

    res1 = ReadoutResonator(
        "rr1",
        intermediate_frequency=50e6,
        outputs=[con1.analog_output(3), con1.analog_output(4)],
        inputs=[con1.analog_input(1), con1.analog_input(2)],
    )
    res1.lo_frequency = 5e9
    res1.time_of_flight = 24

    res2 = ReadoutResonator(
        "rr2",
        intermediate_frequency=50e6,
        outputs=[con2.analog_output(3), con2.analog_output(4)],
        inputs=[con2.analog_input(1), con2.analog_input(2)],
    )
    res2.lo_frequency = 5e9
    res2.time_of_flight = 24

    res3 = ReadoutResonator(
        "rr3",
        intermediate_frequency=50e6,
        outputs=[con3.analog_output(3), con3.analog_output(4)],
        inputs=[con3.analog_input(1), con3.analog_input(2)],
    )
    res3.lo_frequency = 5e9
    res3.time_of_flight = 24

    cb.add(res1)
    cb.add(res2)
    cb.add(res3)

    ro_I = ConstantWaveform("ro_I", 0.01)
    ro_Q = ConstantWaveform("ro_Q", 0.0)

    ro_pulse = MeasurePulse("ro_pulse", [ro_I, ro_Q], 100)

    ro_pulse.add(
        Weights(ConstantIntegrationWeights("cos", cosine=1, sine=0, duration=100))
    )
    ro_pulse.add(
        Weights(
            ConstantIntegrationWeights("minus_sin", cosine=0, sine=-1, duration=100)
        )
    )
    ro_pulse.add(
        Weights(ConstantIntegrationWeights("sin", cosine=0, sine=1, duration=100))
    )

    res1.add(Operation(ro_pulse))
    res2.add(Operation(ro_pulse))
    res3.add(Operation(ro_pulse))

    return cb.build()


def test_load_config(config_3qb_3res):
    config = config_3qb_3res
    try:
        load_config(config)
    except:
        assert False


def test_config_vars():
    c_vars = ConfigVars()
    a = c_vars.parameter("a")

    try:
        a()
    except AssertionError:
        assert True

    c_vars.set(a=3)
    assert a() == 3

    b = c_vars.parameter("a")
    assert b == a

    def setter(a, b):
        return a + b

    c = c_vars.parameter("c", setter=setter)
    assert c(1, 2) == 3


def test_parameter_algebra():
    c_vars = ConfigVars()
    a = c_vars.parameter("a")
    d = a.len
    assert type(d) == Parameter
    c_vars.set(a=[1, 3])
    assert d() == a.len()
    assert a.len() == 2

    c = c_vars.parameter("c")
    d = c_vars.parameter("d")

    c_vars.set(c=4, d=10)
    assert (c + d)() == c() + d()
    assert (c * d)() == c() * d()
    assert (c - d)() == c() - d()
    assert (2 * c)() == 2 * c()
    assert (c / d)() == c() / d()
    assert (c / 10)() == c() / 10
    assert (d ** c)() == 10000
    assert (c ** 2)() == 16
