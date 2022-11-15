from qm import SimulationConfig, LoopbackInterface
from qualang_tools.optimal_weights.TwoStateDiscriminator_alpha import (
    TwoStateDiscriminator,
)
from configuration import *
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
# qmm = QuantumMachinesManager(
#     host="nord-quantique-d14d58b1.quantum-machines.co",
#     port=443,
#     credentials=create_credentials(),
# )
qmm = QuantumMachinesManager(host="172.16.2.103", port="85")
discriminator = TwoStateDiscriminator(
    qmm=qmm,
    config=config,
    readout_el=rr_qe,
    readout_pulse=res_pulse,
    path=f"ge_disc_params_{rr_qe}.npz",
    lsb=lsb,
)


def training_program(
    resonator_el,
    resonator_pulse,
    threshold,
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

        if benchmark:
            state = declare(bool)
            state_st = declare_stream()

        with for_(n, 0, n < n_shots, n + 1):
            reset_frame(resonator_el)
            reset_phase(resonator_el)
            # Wait 100µs for the qubit to decay
            wait(cooldown_time, resonator_el, qubit_element)
            # Measure ground state
            if lsb:
                measure(
                    resonator_pulse,
                    resonator_el,
                    adc,
                    dual_demod.full(weights[0], "out1", weights[2], "out2", I),
                    dual_demod.full(weights[1], "out1", weights[3], "out2", Q),
                )
            else:
                measure(
                    resonator_pulse,
                    resonator_el,
                    adc,
                    dual_demod.full(weights[0], "out1", weights[1], "out2", I),
                    dual_demod.full(weights[2], "out1", weights[3], "out2", Q),
                )
            save(I, I_st)
            save(Q, Q_st)
            if benchmark:
                # State discrimination
                assign(state, I < threshold)
                save(state, state_st)

            # Wait 100µs for the qubit to decay
            wait(cooldown_time, resonator_el, qubit_element)
            # Measure excited state
            # reset_phase(resonator_el)
            align(qubit_element, resonator_el)
            play(pi_pulse, qubit_element)
            align(qubit_element, resonator_el)
            if lsb:
                measure(
                    resonator_pulse * amp(0.998),
                    resonator_el,
                    adc,
                    dual_demod.full(weights[0], "out1", weights[2], "out2", I),
                    dual_demod.full(weights[1], "out1", weights[3], "out2", Q),
                )
            else:
                measure(
                    resonator_pulse * amp(0.998),
                    resonator_el,
                    adc,
                    dual_demod.full(weights[0], "out1", weights[1], "out2", I),
                    dual_demod.full(weights[2], "out1", weights[3], "out2", Q),
                )
            save(I, I_st)
            save(Q, Q_st)
            if benchmark:
                # State discrimination
                assign(state, I < threshold)
                save(state, state_st)
        with stream_processing():
            I_st.save_all("I")
            Q_st.save_all("Q")
            if benchmark:
                state_st.save_all("state")
            else:
                adc.input1().with_timestamps().save_all("adc1")
                adc.input2().save_all("adc2")
    return qua_program


qua_program = training_program(
    rr_qe, res_pulse, 0, "qubit", "x180", 1600, N, ["cos", "sin", "minus_sin", "cos"]
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
    discriminator.saved_data["threshold"],
    "qubit",
    "x180",
    1600,
    N,
    ["opt_cos_rr1a", "opt_sin_rr1a", "opt_minus_sin_rr1a", "opt_cos_rr1a"],
    True,
)
discriminator.benchmark(qua_program=qua_program, n_shots=N)
