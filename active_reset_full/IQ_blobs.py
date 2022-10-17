"""
IQ_blobs.py: template for performing a single shot discrimination and active reset
"""
from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig, LoopbackInterface
from configuration import *
from macros import single_measurement, reset_qubit
from qualang_tools.analysis import two_state_discriminator, DiscriminatorDataclass

from joe_testing.example_reset_comparison import generate_discrimination_data

##############################
# Program-specific variables #
##############################
n_shot = 100  # Number of acquired shots
cooldown_time = 16 #0.0005 * qubit_T1 // 4  # Cooldown time in clock cycles (4ns)

###################
# The QUA program #
###################

qubits = [1, 5, 34]

def generate_reset_program(reset_function_name, reset_function_settings):

    with program() as measure_iq_blobs:
        n = declare(int)  # Averaging index
        Ig_st = [declare_stream() for _ in range(len(qubits))]
        Qg_st = [declare_stream() for _ in range(len(qubits))]
        Ie_st = [declare_stream() for _ in range(len(qubits))]
        Qe_st = [declare_stream() for _ in range(len(qubits))]

        for i, qubit in enumerate(qubits):

            with for_(n, 0, n < n_shot, n + 1):

                # Reset qubit state

                reset_qubit("cooldown_time", cooldown_time=cooldown_time)
                # Measure the ground state
                align("qubit", "resonator")
                I_g, Q_g = single_measurement()
                # Reset qubit state
                reset_qubit(reset_function_settings.get('macro'), **reset_function_settings.get('settings'))
                # Excited state measurement
                align("qubit", "resonator")
                play("pi", "qubit")
                # Measure the excited state
                I_e, Q_e = single_measurement()
                # Save data to the stream processing
                save(I_g, Ig_st[i])
                save(Q_g, Qg_st[i])
                save(I_e, Ie_st[i])
                save(Q_e, Qe_st[i])

            with stream_processing():
                Ig_st[i].with_timestamps().save_all(f"Ig_{i}")
                Qg_st[i].with_timestamps().save_all(f"Qg_{i}")
                Ie_st[i].with_timestamps().save_all(f"Ie_{i}")
                Qe_st[i].with_timestamps().save_all(f"Qe_{i}")

    return measure_iq_blobs


# this works for one qubit only
def run_and_format(reset_program, qmm, simulation=True):
    if simulation:
        return generate_discrimination_data()

        simulation_config = SimulationConfig(
            duration=400000, simulation_interface=LoopbackInterface([("con1", 3, "con1", 1)])
        )
        job = qmm.simulate(config, reset_program, simulation_config)

        results_dataclass_list = []


        for i, qubit in enumerate(qubits):
            results = fetching_tool(job, data_list=[f"Ie_{i}", f"Qe_{i}", f"Ig_{i}", f"Qg_{i}"], mode="wait_for_all")
            # Fetch results

            all_data = results.fetch_all()



            I_g, Q_g, I_e, Q_e = [data['value'] for data in all_data]
            timestamps = [data['timestamp'] for data in all_data][0]

            runtime = (timestamps[-1] - timestamps[0]) / n_shot

            # Plot data
            angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(I_g, Q_g, I_e, Q_e, b_print=False,
                                                                                 b_plot=False)

            results_dataclass = DiscriminatorDataclass(f'Qubit {qubit}', angle, threshold, fidelity, gg, ge, eg, ee, I_g, Q_g, I_e, Q_e)
            results_dataclass.add_attribute('runtime', runtime)
            results_dataclass_list.append(results_dataclass)

        return results_dataclass_list

        # return generate_discrimination_data()

    else:
        qm = qmm.open_qm(config)
        job = qm.execute(reset_program)
        # Get results from QUA program
        results_dataclass_list = []
        for i, qubit in enumerate(qubits):

            results = fetching_tool(job, data_list=[f"Ie_{i}", f"Qe_{i}", f"Ig_{i}", f"Qg_{i}"], mode="wait_for_all")
            # Fetch results
            I_e, Q_e, I_g, Q_g = results.fetch_all()
            # Plot data
            angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(I_g, Q_g, I_e, Q_e, b_print=True, b_plot=True)

            results_dataclass = DiscriminatorDataclass(angle, threshold, fidelity, gg, ge, eg, ee, I_g, Q_g, I_e, Q_e)
            results_dataclass_list.append(results_dataclass)

        return results_dataclass_list



        # If the readout fidelity is satisfactory enough, then the angle and threshold can be updated in the config file.




# if __name__ == '__main__':
#     #####################################
#     #  Open Communication with the QOP  #
#     #####################################
#     qmm = QuantumMachinesManager(qop_ip)
#     measure_iq_blobs = generate_reset_program()
#
#     simulation = False
#     if simulation:
#         simulation_config = SimulationConfig(
#             duration=28000, simulation_interface=LoopbackInterface([("con1", 3, "con1", 1)])
#         )
#         job = qmm.simulate(config, measure_iq_blobs, simulation_config)
#         job.get_simulated_samples().con1.plot()
#     else:
#         qm = qmm.open_qm(config)
#         job = qm.execute(measure_iq_blobs)
#         # Get results from QUA program
#         results = fetching_tool(job, data_list=["Ie", "Qe", "Ig", "Qg"], mode="wait_for_all")
#         # Fetch results
#         I_e, Q_e, I_g, Q_g = results.fetch_all()
#         # Plot data
#         angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(I_g, Q_g, I_e, Q_e, b_print=True, b_plot=True)
#         # If the readout fidelity is satisfactory enough, then the angle and threshold can be updated in the config file.
