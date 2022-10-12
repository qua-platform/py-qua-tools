"""
T1.py: Measures T1
"""
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from configuration import *
import matplotlib.pyplot as plt
import numpy as np
from qm import SimulationConfig
from qualang_tools.loops import from_array

from qm.simulate.credentials import create_credentials

import logging
logging.basicConfig(level='INFO')
logger = logging.getLogger(__name__)

###################
# The QUA program #
###################

tau_min = 4  # in clock cycles
tau_max = 100  # in clock cycles
d_tau = 2  # in clock cycles
taus = np.arange(tau_min, tau_max + 0.1, d_tau)  # + 0.1 to add t_max to taus

n_avg = 1e4
cooldown_time = 5 * qubit_T1 // 4

with program() as T1:
    n = declare(int)
    n_st = declare_stream()
    I = declare(fixed)
    I_st = declare_stream()
    Q = declare(fixed)
    Q_st = declare_stream()
    tau = declare(int)

    with for_(n, 0, n < n_avg, n + 1):
        with for_(*from_array(tau, taus)):
            play("pi", "qubit")
            wait(tau, "qubit")
            align("qubit", "resonator")
            measure(
                "readout",
                "resonator",
                None,
                dual_demod.full("cos", "out1", "sin", "out2", I),
                dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
            )
            save(I, I_st)
            save(Q, Q_st)
            wait(cooldown_time, "resonator")
        save(n, n_st)

    with stream_processing():
        I_st.buffer(len(taus)).average().save("I")
        Q_st.buffer(len(taus)).average().save("Q")
        n_st.save("iteration")

#####################################
#  Open Communication with the QOP  #
#####################################
logger.info('connecting to qmm...')
qmm = QuantumMachinesManager(
    host="theo-4c195fa0.dev.quantum-machines.co",
    port=443,
    credentials=create_credentials())
logger.info('connected.')

#######################
# Simulate or execute #
#######################

simulate = True

if simulate:
    logger.info("simulating")
    simulation_config = SimulationConfig(duration=1000)  # in clock cycles

    logger.info('simulation config loaded')
    job = qmm.simulate(config, T1, simulation_config)

    logger.info('job executed')

    job.get_simulated_samples().con1.plot()

else:
    qm = qmm.open_qm(config)

    job = qm.execute(T1)
    # Get results from QUA program
    results = fetching_tool(job, data_list=["I", "Q", "iteration"], mode="live")
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    while results.is_processing():
        # Fetch results
        I, Q, iteration = results.fetch_all()
        # Progress bar
        progress_counter(iteration, n_avg, start_time=results.get_start_time())
        # Plot results
        plt.cla()
        plt.plot(4 * taus, I, ".", label="I")
        plt.plot(4 * taus, Q, ".", label="Q")
        plt.xlabel("Decay time [ns]")
        plt.ylabel("I & Q amplitude [a.u.]")
        plt.title("T1 measurement")
        plt.legend()
        plt.pause(0.1)