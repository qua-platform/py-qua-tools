from qm import SimulationConfig, LoopbackInterface
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
import numpy as np
from qualang_tools.optimal_weights.TwoStateDiscriminator import TwoStateDiscriminator
import pytest
from copy import deepcopy


@pytest.fixture
def config():

    def simulate_pulse(IF_freq, chi, k, Ts, Td, power):
        I = [0]
        Q = [0]

        for t in range(Ts):
            I.append(I[-1] + (power / 2 - k * I[-1] + Q[-1] * chi))
            Q.append(Q[-1] + (power / 2 - k * Q[-1] - I[-1] * chi))

        for t in range(Td - 1):
            I.append(I[-1] + (-k * I[-1] + Q[-1] * chi))
            Q.append(Q[-1] + (-k * Q[-1] - I[-1] * chi))

        I = np.array(I)
        Q = np.array(Q)
        t = np.arange(len(I))

        S = I * np.cos(2 * np.pi * IF_freq * t * 1e-9) + Q * np.sin(2 * np.pi * IF_freq * t * 1e-9)

        return t, I, Q, S

    resonators_lo = 7.1e9  # High Band Pass
    WG1_lo = resonators_lo
    WG2_lo = resonators_lo
    q1a_res_IF = 40e6
    q2a_res_IF = 50e6

    readout_len = 480
    IF_freq = q1a_res_IF
    Ts = readout_len - 200
    Td = 200
    power = 0.2
    k = 0.04
    chi = 0.023
    [tg_, Ig_, Qg_, Sg_] = simulate_pulse(IF_freq, 1 * chi, k, Ts, Td, power)
    [te_, Ie_, Qe_, Se_] = simulate_pulse(IF_freq, 3 * chi, k, Ts, Td, power)
    [tf_, If_, Qf_, Sf_] = simulate_pulse(IF_freq, 5 * chi, k, Ts, Td, power)

    divide_signal_factor = 100
    smearing = 60

    return {

        'version': 1,

        'controllers': {

            'con1': {
                'type': 'opx1',
                'analog_outputs': {
                    1: {'offset': 0.0},
                    2: {'offset': 0.0},
                },
                'digital_outputs': {
                    1: {},
                },
                'analog_inputs': {
                    1: {'offset': 0.0},
                    2: {'offset': 0.0},
                }
            },
        },

        'elements': {

            # readout resonators:
            'rr1a': {
                'mixInputs': {
                    'I': ('con1', 1),
                    'Q': ('con1', 2),
                    'lo_frequency': WG1_lo,
                    'mixer': 'mixer_WG1',
                },
                'intermediate_frequency': q1a_res_IF,
                'operations': {
                    'readout': 'readout_pulse_q1a',
                    'readout_pulse_g': 'readout_pulse_g',
                    'readout_pulse_e': 'readout_pulse_e',
                    'readout_pulse_f': 'readout_pulse_f'
                },
                'outputs': {
                    'out1': ('con1', 1),
                    'out2': ('con1', 2),
                },
                'time_of_flight': 188,
                'smearing': smearing,
            },

            'rr2a': {
                'mixInputs': {
                    'I': ('con1', 1),
                    'Q': ('con1', 2),
                    'lo_frequency': WG2_lo,
                    'mixer': 'mixer_WG2',
                },
                'intermediate_frequency': q2a_res_IF,
                'operations': {
                    'readout': 'readout_pulse_q1a',
                    'readout_pulse_g': 'readout_pulse_g',
                    'readout_pulse_e': 'readout_pulse_e',
                    'readout_pulse_f': 'readout_pulse_f'
                },
                'outputs': {
                    'out1': ('con1', 1),
                    'out2': ('con1', 2),
                },
                'time_of_flight': 188,
                'smearing': 0,
            },

        },

        'pulses': {

            'readout_pulse_q1a': {
                'operation': 'measurement',
                'length': readout_len,
                'waveforms': {
                    'I': 'ro_wf_q1a',
                    'Q': 'zero_wf'
                },
                'integration_weights': {
                    'cos': 'cos_weights',
                    'sin': 'sin_weights',
                    'minus_sin': 'minus_sin_weights',
                },
                'digital_marker': 'ON'
            },

            'readout_pulse_g': {
                'operation': 'measurement',
                'length': readout_len,
                'waveforms': {
                    'I': 'Ig_wf',
                    'Q': 'Qg_wf'
                },
                'integration_weights': {
                    'cos': 'cos_weights',
                    'sin': 'sin_weights',
                    'minus_sin': 'minus_sin_weights',
                },
                'digital_marker': 'ON'
            },

            'readout_pulse_e': {
                'operation': 'measurement',
                'length': readout_len,
                'waveforms': {
                    'I': 'Ie_wf',
                    'Q': 'Qe_wf'
                },
                'integration_weights': {
                    'cos': 'cos_weights',
                    'sin': 'sin_weights',
                    'minus_sin': 'minus_sin_weights',
                },
                'digital_marker': 'ON'
            },

            'readout_pulse_f': {
                'operation': 'measurement',
                'length': readout_len,
                'waveforms': {
                    'I': 'If_wf',
                    'Q': 'Qf_wf'
                },
                'integration_weights': {
                    'cos': 'cos_weights',
                    'sin': 'sin_weights',
                    'minus_sin': 'minus_sin_weights',
                },
                'digital_marker': 'ON'
            },

        },

        'waveforms': {

            'zero_wf': {
                'type': 'constant',
                'sample': 0.0
            },

            'ro_wf_q1a': {
                'type': 'constant',
                'sample': 0.11
            },

            'Ig_wf': {
                'type': 'arbitrary',
                'samples': [float(arg / divide_signal_factor) for arg in Ig_]
            },

            'Qg_wf': {
                'type': 'arbitrary',
                'samples': [float(arg / divide_signal_factor) for arg in Qg_]
            },

            'Ie_wf': {
                'type': 'arbitrary',
                'samples': [float(arg / divide_signal_factor) for arg in Ie_]
            },

            'Qe_wf': {
                'type': 'arbitrary',
                'samples': [float(arg / divide_signal_factor) for arg in Qe_]
            },

            'If_wf': {
                'type': 'arbitrary',
                'samples': [float(arg / divide_signal_factor) for arg in If_]
            },

            'Qf_wf': {
                'type': 'arbitrary',
                'samples': [float(arg / divide_signal_factor) for arg in Qf_]
            },

        },

        'digital_waveforms': {

            'ON': {
                'samples': [(1, 0)]
            },
        },

        'integration_weights': {

            'cos_weights': {
                "cosine": [(1.0, readout_len)],  # Previous format for versions before 1.20: [1.0] * readout_len
                "sine": [(0.0, readout_len)],
            },

            'sin_weights': {
                "cosine": [(0.0, readout_len)],
                "sine": [(1.0, readout_len)],
            },

            'minus_sin_weights': {
                "cosine": [(0.0, readout_len)],
                "sine": [(-1.0, readout_len)],
            },

        },

        'mixers': {
            'mixer_WG1': [
                {'intermediate_frequency': q1a_res_IF, 'lo_frequency': WG1_lo, 'correction': [1, 0, 0, 1]},
            ],

            'mixer_WG2': [
                {'intermediate_frequency': q2a_res_IF, 'lo_frequency': WG2_lo, 'correction': [1, 0, 0, 1]},
            ],
        }
    }


def test_opt_weight_training(config):
    cfg = deepcopy(config)

    N = 100
    wait_time = 10
    readout_len = 480
    smearing = 60
    lsb = True
    resonator_el = 'rr1a'
    resonator_pulse = 'readout_pulse_g'
    resonator_pulse_aux = 'readout_pulse_e'
    qmm = QuantumMachinesManager()
    discriminator = TwoStateDiscriminator(qmm=qmm,
                                          config=cfg,
                                          update_tof=False,
                                          resonator_el=resonator_el,
                                          resonator_pulse=resonator_pulse,
                                          path=f'ge_disc_params_{resonator_el}.npz',
                                          meas_len=readout_len,
                                          smearing=smearing,
                                          lsb=lsb,
                                          resonator_pulse_aux=resonator_pulse_aux)

    if not lsb:
        simulation_config = SimulationConfig(
            duration=60000,
            simulation_interface=LoopbackInterface(
                [("con1", 1, "con1", 1), ("con1", 2, "con1", 2)], latency=230, noisePower=0.07 ** 2
            )
        )
    else:
        simulation_config = SimulationConfig(
            duration=60000,
            simulation_interface=LoopbackInterface(
                [("con1", 1, "con1", 2), ("con1", 2, "con1", 1)], latency=230, noisePower=0.07 ** 2
            )
        )

    def training_measurement(readout_pulse):
        if not lsb:
            measure(readout_pulse, resonator_el, adc_st,
                    dual_demod.full('cos', 'out1', 'sin', 'out2', I),
                    dual_demod.full('minus_sin', 'out1', 'cos', 'out2', Q))
        else:
            measure(readout_pulse, resonator_el, adc_st,
                    dual_demod.full('cos', 'out1', 'minus_sin', 'out2', I),
                    dual_demod.full('sin', 'out1', 'cos', 'out2', Q))

    with program() as training_program:
        n = declare(int)
        I = declare(fixed)
        Q = declare(fixed, value=0)

        I_st = declare_stream()
        Q_st = declare_stream()
        adc_st = declare_stream(adc_trace=True)

        with for_(n, 0, n < N, n + 1):
            wait(wait_time, resonator_el)
            training_measurement("readout_pulse_g")
            save(I, I_st)
            save(Q, Q_st)

            wait(wait_time, resonator_el)
            training_measurement("readout_pulse_e")
            save(I, I_st)
            save(Q, Q_st)

        with stream_processing():
            I_st.save_all('I')
            Q_st.save_all('Q')
            adc_st.input1().with_timestamps().save_all("adc1")
            adc_st.input2().save_all("adc2")

    discriminator.train(program=training_program, plot=True, dry_run=True, simulate=simulation_config)