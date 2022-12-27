from qm import SimulationConfig, LoopbackInterface
from qualang_tools.optimal_weights.TwoStateDiscriminator_alpha import (
    TwoStateDiscriminator,
)
from configuration_ir_mixer import *
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
import matplotlib.pyplot as plt
import numpy as np
from qm.simulate.credentials import create_credentials

N = 100
wait_time = 10
lsb = False
rr_qe = "rr1a"
res_pulse = "readout_pulse_g"
angle = 6
nangle = 90 - angle
# qmm = QuantumMachinesManager(
#     host="nord-quantique-d14d58b1.quantum-machines.co",
#     port=443,
#     credentials=create_credentials(),
# )
qmm = QuantumMachinesManager(host="172.16.2.103", port="81")
discriminator = TwoStateDiscriminator(
    qmm=qmm,
    config=config,
    readout_el=rr_qe,
    readout_pulse=res_pulse,
    path=f"ge_disc_params_{rr_qe}.npz",
    lsb=lsb,
    iq_mixer=False,
)


def training_program(
    resonator_el,
    resonator_pulse,
    qubit_element,
    pi_pulse,
    cooldown_time,
    n_shots,
    weights,
    benchmark: bool = False,
):
    with program() as qua_program:
        n = declare(int)
        I = declare(fixed)
        Q = declare(fixed)
        I_st = declare_stream()
        Q_st = declare_stream()
        adc = declare_stream(adc_trace=True)

        with for_(n, 0, n < n_shots, n + 1):
            # Wait 100µs for the qubit to decay
            wait(cooldown_time, resonator_el, qubit_element)
            # Measure ground state
            if lsb:
                measure(
                    resonator_pulse,
                    resonator_el,
                    adc,
                    demod.full(weights[0], I,  "out1"),
                    demod.full(weights[1], Q, "out1"),
                )
            else:
                measure(
                    resonator_pulse,
                    resonator_el,
                    adc,
                    demod.full(weights[0], I,  "out1"),
                    demod.full(weights[1], Q, "out1"),
                )
            save(I, I_st)
            save(Q, Q_st)

            # Wait 100µs for the qubit to decay
            wait(cooldown_time, resonator_el, qubit_element)
            # Measure excited state
            align(qubit_element, resonator_el)
            play(pi_pulse, qubit_element)
            align(qubit_element, resonator_el)
            if lsb:
                measure(
                    resonator_pulse
                    * amp(
                        np.cos((angle / 180) * np.pi),
                        np.cos((nangle / 180) * np.pi),
                        np.cos((nangle / 180) * np.pi),
                        np.cos((angle / 180) * np.pi),
                    ),
                    resonator_el,
                    adc,
                    demod.full(weights[0], I,  "out1"),
                    demod.full(weights[1], Q, "out1"),
                )
            else:
                measure(
                    resonator_pulse
                    * amp(
                        np.cos((angle / 180) * np.pi),
                        np.cos((nangle / 180) * np.pi),
                        np.cos((nangle / 180) * np.pi),
                        np.cos((angle / 180) * np.pi),
                    ),
                    resonator_el,
                    adc,
                    demod.full(weights[0], I,  "out1"),
                    demod.full(weights[1], Q, "out1"),
                )
            save(I, I_st)
            save(Q, Q_st)

        with stream_processing():
            I_st.save_all("I")
            Q_st.save_all("Q")
            adc.input1().with_timestamps().save_all("adc1")
            # adc.input2().save_all("adc2")

    return qua_program


qua_program = training_program(
    rr_qe,
    res_pulse,
    "qubit",
    "x180",
    1600,
    N,
    ["cos", "sin", "minus_sin", "cos"],
)

# gives you a template for training program
discriminator.get_default_training_program()
# Training
discriminator.train(
    qua_program=qua_program, plot=True, n_shots=N, correction_method="mean"
)
qua_program = training_program(
    rr_qe,
    res_pulse,
    "qubit",
    "x180",
    1600,
    N,
    ["opt_cos_rr1a", "opt_sin_rr1a", "opt_minus_sin_rr1a", "opt_cos_rr1a"],
    False,
)
discriminator.benchmark(qua_program=qua_program, n_shots=N)
