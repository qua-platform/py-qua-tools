import numpy as np
from matplotlib import pyplot as plt
from qm.qua import *

from qualang_tools.loops import from_array
from qualang_tools.simulator.quantum.simulate import simulate_program
from qualang_tools.units import unit


def test_ramsey_virtual_detuning(transmon_pair_backend, transmon_pair_qua_config, config_to_transmon_pair_backend_map):
    n_avg = 1
    # Dephasing time sweep (in clock cycles = 4ns) - minimum is 4 clock cycles
    tau_min = 4
    tau_max = 2000 // 4
    d_tau = 40 // 4
    taus = np.arange(tau_min, tau_max + 0.1, d_tau)  # + 0.1 to add tau_max to taus
    # Detuning converted into virtual Z-rotations to observe Ramsey oscillation and get the qubit frequency
    u = unit()
    detuning = 1 * u.MHz  # in Hz
    thermalization_time = 16
    ge_threshold = 0

    with program() as ramsey:
        n = declare(int)  # QUA variable for the averaging loop
        tau = declare(int)  # QUA variable for the idle time
        phase = declare(fixed)  # QUA variable for dephasing the second pi/2 pulse (virtual Z-rotation)
        I = declare(fixed)  # QUA variable for the measured 'I' quadrature
        Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
        state = declare(bool)  # QUA variable for the qubit state
        I_st = declare_stream()  # Stream for the 'I' quadrature
        Q_st = declare_stream()  # Stream for the 'Q' quadrature
        state_st = declare_stream()  # Stream for the qubit state
        n_st = declare_stream()  # Stream for the averaging iteration 'n'

        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(tau, taus)):
                # Rotate the frame of the second x90 gate to implement a virtual Z-rotation
                # 4*tau because tau was in clock cycles and 1e-9 because tau is ns
                assign(phase, Cast.mul_fixed_by_int(detuning * 1e-9, 4 * tau))
                # Strict_timing ensures that the sequence will be played without gaps
                with strict_timing_():
                    # 1st x90 gate
                    play("x90", "qubit_1")
                    # Wait a varying idle time
                    wait(tau, "qubit_1")
                    # Rotate the frame of the second x90 gate to implement a virtual Z-rotation
                    frame_rotation_2pi(phase, "qubit_1")
                    # 2nd x90 gate
                    play("x90", "qubit_1")
                # Align the two elements to measure after playing the qubit pulse.
                align("qubit_1", "resonator_1")
                # Measure the state of the resonator
                measure("readout", "resonator_1", None)
                # Wait for the qubit to decay to the ground state
                wait(thermalization_time * u.ns, "resonator_1")
                # State discrimination
                assign(state, I > ge_threshold)
                # Save the 'I', 'Q' and 'state' to their respective streams
                save(I, I_st)
                save(Q, Q_st)
                save(state, state_st)
                # Reset the frame of the qubit in order not to accumulate rotations
                reset_frame("qubit_1")
            # Save the averaging iteration to get the progress bar
            save(n, n_st)

        with stream_processing():
            # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
            I_st.buffer(len(taus)).average().save("I")
            Q_st.buffer(len(taus)).average().save("Q")
            state_st.boolean_to_int().buffer(len(taus)).average().save("state")
            n_st.save("iteration")

    results = simulate_program(
        qua_program=ramsey,
        qua_config=transmon_pair_qua_config,
        qua_config_to_backend_map=config_to_transmon_pair_backend_map,
        backend=transmon_pair_backend,
        num_shots=10_000,
        plot_second_schedule=True
    )
    plt.show()

    state_probabilities = np.array(results[0])
    time = np.arange(tau_min*4, tau_max*4, d_tau*4) * 1e-9  # ns
    freq = 1e6  # 1 MHz
    expected_state_probabilities = np.sin(np.pi*freq*time) ** 2

    # make sure no single point is different to expected within 0.1 tolerance
    assert np.allclose(state_probabilities, expected_state_probabilities, atol=0.1)

    for i, result in enumerate(results):
        plt.plot(4*taus, results[i], label=f"Simulated Q{i}")
        plt.plot(4*taus, expected_state_probabilities, label=f"Expected Q{i}")
        plt.ylim(-0.05, 1.05)
    plt.xlabel("Time [ns]")
    plt.legend()
    plt.show()


# def test_ramsey_real_detuning(transmon_pair_backend, transmon_pair_qua_config, config_to_transmon_pair_backend_map):
#     n_avg = 1000
#     # Dephasing time sweep (in clock cycles = 4ns) - minimum is 4 clock cycles
#     tau_min = 4
#     tau_max = 2000 // 4
#     d_tau = 40 // 4
#     taus = np.arange(tau_min, tau_max + 0.1, d_tau)  # + 0.1 to add tau_max to taus
#     u = unit()
#     # Detuning converted into virtual Z-rotations to observe Ramsey oscillation and get the qubit frequency
#     detuning = 1 * u.MHz  # in Hz
#     thermalization_time = 16
#
#     with program() as ramsey:
#         n = declare(int)  # QUA variable for the averaging loop
#         tau = declare(int)  # QUA variable for the idle time
#         I = declare(fixed)  # QUA variable for the measured 'I' quadrature
#         Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
#         I_st = declare_stream()  # Stream for the 'I' quadrature
#         Q_st = declare_stream()  # Stream for the 'Q' quadrature
#         n_st = declare_stream()  # Stream for the averaging iteration 'n'
#
#         # Shift the qubit drive frequency to observe Ramsey oscillations
#         update_frequency("qubit", qubit_IF + detuning)
#
#         with for_(n, 0, n < n_avg, n + 1):
#             with for_(*from_array(tau, taus)):
#                 # 1st x90 gate
#                 play("x90", "qubit")
#                 # Wait a varying idle time
#                 wait(tau, "qubit")
#                 # 2nd x90 gate
#                 play("x90", "qubit")
#                 # Align the two elements to measure after playing the qubit pulse.
#                 align("qubit", "resonator")
#                 # Measure the state of the resonator
#                 measure(
#                     "readout",
#                     "resonator",
#                     None,
#                     dual_demod.full("rotated_cos", "out1", "rotated_sin", "out2", I),
#                     dual_demod.full("rotated_minus_sin", "out1", "rotated_cos", "out2", Q),
#                 )
#                 # Wait for the qubit to decay to the ground state
#                 wait(thermalization_time * u.ns, "resonator")
#                 # Save the 'I' & 'Q' quadratures to their respective streams
#                 save(I, I_st)
#                 save(Q, Q_st)
#             # Save the averaging iteration to get the progress bar
#             save(n, n_st)
#
#         with stream_processing():
#             # Cast the data into a 1D vector, average the 1D vectors together and store the results on the OPX processor
#             I_st.buffer(len(taus)).average().save("I")
#             Q_st.buffer(len(taus)).average().save("Q")
#             n_st.save("iteration")
#
#     results = simulate(
#         qua_program=ramsey,
#         qua_config=transmon_pair_qua_config,
#         qua_config_to_backend_map=config_to_transmon_pair_backend_map,
#         backend=transmon_pair_backend,
#         num_shots=10_000
#     )
#
#     for i, result in enumerate(results):
#         plt.plot(taus, results[i], label=f"Q{i}")
#         plt.ylim(-0.05, 1.05)
#     plt.legend()
#     plt.show()
#
