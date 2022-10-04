import pytest
import numpy as np
from qualang_tools.config.helper_tools import *
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
import matplotlib.pyplot as plt
from scipy import signal
from qm import SimulationConfig

def config0():
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
                "analog_outputs": {1: {"offset": 0.0}, 2: {"offset": 0.0}, 3: {"offset": 0.0},4: {"offset": 0.0}, 5: {"offset": 0.0}},
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
                "operations": {

                },
            },
            "resonator": {
                "mixInputs": {
                    "I": ("con1", 4),
                    "Q": ("con1", 5),
                    "lo_frequency": 0,
                    "mixer": "mixer_qubit",
                },
                "intermediate_frequency": 100e6,
                "operations": {
                    "readout": "readout_pulse"
                },
                "outputs": {
                    "out1": ("con1", 1),
                    "out2": ("con1", 2),
                },
                "time_of_flight": 24,
                "smearing": 0,
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
                    "minus_sin": "minus_sine_weights"
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

conf = config0()
config = QuaConfig(conf)

config.add_control_operation_iq("qubit", "gate", [0.1 for _ in range(112)], [0.1 for _ in range(112)])
config.add_control_operation_iq("resonator", "long_readout", [0.1 for _ in range(112)], [0.0 for _ in range(112)])
config.update_integration_weight("resonator", "readout", "cos", [(1, 80)], [(0, 80)])
config.update_integration_weight("resonator", "readout", "sin", [(0, 80)], [(1, 80)])
config.update_integration_weight("resonator", "readout", "minus_sin", [(0, 80)], [(-1, 80)])
# config.update_op_amp("resonator", "long_readout", 0.25)
config.reset()

n_avg = 100

cooldown_time = 16  // 4

f_min = 30e6
f_max = 70e6
df = 0.5e6
freqs = np.arange(f_min, f_max + 0.1, df)  # + 0.1 to add f_max to freqs

with program() as resonator_spec:
    n = declare(int)
    f = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    adc = declare_stream(adc_trace=True)

    with for_(n, 0, n < n_avg, n + 1):
        with for_(f, f_min, f <= f_max, f + df):  # Notice it's <= to include f_max (This is only for integers!)
            update_frequency("qubit", f)
            play("gate", "qubit")
            measure(
                "readout",
                "resonator",
                None,
                dual_demod.full("cos", "out1", "sin", "out2", I),
                dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
            )
            wait(cooldown_time, "resonator")
            save(I, I_st)
            save(Q, Q_st)

    with stream_processing():
        I_st.buffer(len(freqs)).average().save("I")
        Q_st.buffer(len(freqs)).average().save("Q")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host="172.16.2.103", port=85)

#######################
# Simulate or execute #
#######################

simulate = True

if simulate:
    simulation_config = SimulationConfig(duration=1000)
    job = qmm.simulate(config, resonator_spec, simulation_config)
    job.get_simulated_samples().con1.plot()

else:
    qm = qmm.open_qm(config)
    job = qm.execute(resonator_spec)

    # Get results from QUA program
    res_handles = job.result_handles
    I_handles = res_handles.get("I")
    Q_handles = res_handles.get("Q")
    I_handles.wait_for_values(1)
    Q_handles.wait_for_values(1)
    # Live plotting
    fig = plt.figure()
    while job.result_handles.is_processing():
        # Fetch results
        I = res_handles.get("I").fetch_all()
        Q = res_handles.get("Q").fetch_all()
        # Plot results
        plt.subplot(211)
        plt.cla()
        plt.title("resonator spectroscopy amplitude")
        plt.plot(freqs, np.sqrt(I**2 + Q**2), ".")
        plt.xlabel("frequency [MHz]")
        plt.ylabel(r"$\sqrt{I^2 + Q^2}$ [a.u.]")
        plt.subplot(212)
        plt.cla()
        # detrend removes the linear increase of phase
        phase = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))
        plt.title("resonator spectroscopy phase")
        plt.plot(freqs, phase, ".")
        plt.xlabel("frequency [MHz]")
        plt.ylabel("Phase [rad]")
        plt.pause(0.1)
        plt.tight_layout()

    # Fetch results
    I = res_handles.get("I").fetch_all()
    Q = res_handles.get("Q").fetch_all()
    # 1D spectroscopy plot
    plt.clf()
    plt.subplot(211)
    plt.title("resonator spectroscopy amplitude [V]")
    plt.plot(freqs, np.sqrt(I**2 + Q**2), ".")
    plt.xlabel("frequency [MHz]")
    plt.ylabel(r"$\sqrt{I^2 + Q^2}$ [a.u.]")
    plt.subplot(212)
    # detrend removes the linear increase of phase
    phase = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))
    plt.title("resonator spectroscopy phase [rad]")
    plt.plot(freqs, phase, ".")
    plt.xlabel("frequency [MHz]")
    plt.ylabel("Phase [rad]")
    plt.tight_layout()
