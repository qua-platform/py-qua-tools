from qm.qua import *
from qm import QuantumMachinesManager
from qm import SimulationConfig
from configuration_lf import *
from qualang_tools.results import progress_counter, fetching_tool
from qualang_tools.plot import interrupt_on_close
from qualang_tools.loops import from_array
from qualang_tools.addons.variables import assign_variables_to_element
import matplotlib.pyplot as plt


###################
# The QUA program #
###################

n_avg = 1000
# Pulse duration sweep in ns - must be larger than 4 clock cycles
durations = np.arange(52, 200, 4)
# Pulse amplitude sweep (as a pre-factor of the qubit pulse amplitude) - must be within [-2; 2)
ramp_durations = np.arange(16, 200, 4)

# Add the relevant voltage points describing the "slow" sequence (no qubit pulse)
seq = VoltageGateSequence(config, ["P1_sticky", "P2_sticky"])
seq.add_points("initialization", level_init, duration_init)
seq.add_points("idle", level_manip, duration_manip)
seq.add_points("readout", level_readout, duration_readout)

with program() as Landau_Zener_prog:
    n = declare(int)  # QUA integer used as an index for the averaging loop
    t = declare(int)  # QUA variable for the qubit pulse duration
    t_R = declare(int)  # QUA variable for the qubit drive amplitude pre-factor
    rate = declare(fixed)  # QUA variable for the qubit drive amplitude pre-factor
    n_st = declare_stream()  # Stream for the iteration number (progress bar)

    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    dc_signal = declare(fixed)  # QUA variable for the measured dc signal
    I_st = declare_stream()  # Stream for the iteration number (progress bar)
    Q_st = declare_stream()  # Stream for the iteration number (progress bar)
    dc_signal_st = declare_stream()  # Stream for the iteration number (progress bar)

    # Ensure that the result variables are assigned to the measurement elements
    assign_variables_to_element("tank_circuit", I, Q)
    assign_variables_to_element("TIA", dc_signal)

    with for_(n, 0, n < n_avg, n + 1):  # The averaging loop
        save(n, n_st)
        with for_(*from_array(t, durations)):  # Loop over the interaction duration
            # Here a python for loop is used to prevent gaps coming from dynamically changing the ramp rate, the ramp
            # duration and the duration of the next pulse in QUA.

            # for t_R in ramp_durations:  # Loop over the ramp duration
            with for_(*from_array(t_R, ramp_durations)):
                t_R = 16
                # t = 200
                align()
                # Navigate through the charge stability map
                seq.add_step(voltage_point_name="initialization")
                seq.add_step(voltage_point_name="idle", ramp_duration=t_R, duration=t)
                seq.add_step(voltage_point_name="readout", ramp_duration=t_R, duration=t)
                seq.add_compensation_pulse()
                # Measure the dot right after the qubit manipulation
                # wait(duration_init * u.ns + 2*(t_R>>2) + (t >> 2), "tank_circuit")
                # measure("readout", "tank_circuit", None)
                seq.ramp_to_zero()


#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config)
from qm.qua import *
import matplotlib.pyplot as plt
from scipy.signal import butter, lfilter
from typing import Union
from numpy.typing import NDArray
import numpy as np


def round_to_fixed(x, number_of_bits=12):
    """
    function which rounds 'x' to 'number_of_bits' of precision to help reduce the accumulation of fixed point arithmetic errors
    """
    return round((2**number_of_bits) * x) / (2**number_of_bits)


def get_filtered_voltage(
    voltage_list: Union[NDArray, list], step_duration: float, bias_tee_cut_off_frequency: float, plot: bool = False
):
    """Get the voltage after filtering through the bias-tee

    :param voltage_list: List of voltages outputted by the OPX in V.
    :param step_duration: Duration of each step in s.
    :param bias_tee_cut_off_frequency: Cut-off frequency of the bias-tee in Hz.
    :param plot: Flag to plot the voltage values if set to True.
    :return: the filtered and unfiltered voltage lists with 1Gs/s sampling rate.
    """

    def high_pass(data, f_cutoff):
        res = butter(1, f_cutoff, btype="high", analog=False)
        return lfilter(res[0], res[1], data)

    y = [val for val in voltage_list for _ in range(int(step_duration * 1e9))]
    y_filtered = high_pass(y, bias_tee_cut_off_frequency * 1e-9)
    if plot:
        # plt.figure()
        plt.plot(y, label="before bias-tee")
        plt.plot(y_filtered, label="after bias-tee")
        plt.xlabel("Time [ns]")
        plt.ylabel("Voltage [V]")
        plt.legend()
    print(f"Error: {np.mean(np.abs((y-y_filtered)/(max(y)-min(y))))*100:.2f} %")
    return y, y_filtered


###########################
# Run or Simulate Program #
###########################

simulate = True

if simulate:
    # Simulates the QUA program for the specified duration
    simulation_config = SimulationConfig(duration=100000 // 4)  # In clock cycles = 4ns
    # Simulate blocks python until the simulation is done
    job = qmm.simulate(config, Landau_Zener_prog, simulation_config)
    # Plot the simulated samples
    plt.figure()
    plt.subplot(211)
    job.get_simulated_samples().con1.plot()
    plt.axhline(level_init[0], color="k", linestyle="--")
    plt.axhline(level_manip[0], color="k", linestyle="--")
    plt.axhline(level_readout[0], color="k", linestyle="--")
    plt.axhline(level_init[1], color="k", linestyle="--")
    plt.axhline(level_manip[1], color="k", linestyle="--")
    plt.axhline(level_readout[1], color="k", linestyle="--")
    # plt.yticks(
    #     [
    #         level_readout[1],
    #         level_manip[1],
    #         level_init[1],
    #         0.0,
    #         level_init[0],
    #         level_manip[0],
    #         level_readout[0],
    #     ],
    #     ["readout", "manip", "init", "0", "init", "manip", "readout"],
    # )
    plt.legend("")
    plt.subplot(212)
    get_filtered_voltage(job.get_simulated_samples().con1.analog["1"], 1e-9, 10000, True)

else:
    # Open a quantum machine to execute the QUA program
    qm = qmm.open_qm(config)
    # Send the QUA program to the OPX, which compiles and executes it - Execute does not block python!
    job = qm.execute(Landau_Zener_prog)
    # Get results from QUA program and initialize live plotting
    results = fetching_tool(job, data_list=["I", "Q", "dc_signal", "iteration"], mode="live")
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
    while results.is_processing():
        # Fetch the data from the last OPX run corresponding to the current slow axis iteration
        I, Q, DC_signal, iteration = results.fetch_all()
        # Convert results into Volts
        S = u.demod2volts(I + 1j * Q, reflectometry_readout_length, single_demod=True)
        R = np.abs(S)  # Amplitude
        phase = np.angle(S)  # Phase
        DC_signal = u.demod2volts(DC_signal, readout_len, single_demod=True)
        # Progress bar
        progress_counter(iteration, n_avg)
        # Plot data
        plt.subplot(121)
        plt.cla()
        plt.title(r"$R=\sqrt{I^2 + Q^2}$ [V]")
        plt.pcolor(ramp_durations, durations, R)
        plt.xlabel("Ramp duration [ns]")
        plt.ylabel("Interaction pulse duration [ns]")
        plt.subplot(122)
        plt.cla()
        plt.title("Phase [rad]")
        plt.pcolor(ramp_durations, durations, phase)
        plt.xlabel("Ramp duration [ns]")
        plt.ylabel("Interaction duration [ns]")
        plt.tight_layout()
        plt.pause(0.1)
