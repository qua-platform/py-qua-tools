"""
        QUBIT SPECTROSCOPY OVER A WIDE RANGE (OUTER LOOP)
This procedure conducts a broad 1D frequency sweep of the qubit, measuring the resonator while sweeping an
external LO source simultaneously. The external LO source is swept in the outer loop to optimize run time.
Users should update the LO source frequency using the provided API at the end of the script
(lo_source.set_freq(freqs_external[i])).

Prerequisites:
    -Identification of the resonator's resonance frequency when coupled to the qubit being studied (referred to as "resonator_spectroscopy").
    -Calibration of the IQ mixer connected to the qubit drive line (be it an external mixer or an Octave port).
    -Configuration of the saturation pulse amplitude and duration to transition the qubit into a mixed state.

Before proceeding to the next node:
    -Adjust the qubit frequency settings, labeled as "qubit_IF" and "qubit_LO", in the configuration.
"""

from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from configuration import *
from qualang_tools.results import progress_counter, wait_until_job_is_paused
from qualang_tools.plot import interrupt_on_close
from qualang_tools.loops import from_array
from qualang_tools.octave_tools import get_calibration_parameters, set_correction_parameters
import matplotlib.pyplot as plt
from time import sleep
from qm import generate_qua_script



###################
# The QUA program #
###################

n_avg = 100  # The number of averages
# The intermediate frequency sweep parameters
f_min = 1 * u.MHz
f_max = 251 * u.MHz
df = 2000 * u.kHz
frequencies = np.arange(
    f_min, f_max + 0.1, df
)  # The intermediate frequency vector (+ 0.1 to add f_max to frequencies)
config["elements"]["qubit"]["intermediate_frequency"] = frequencies[
    len(frequencies) // 2
]

# The LO frequency sweep parameters
f_min_external = 4.501e9 - f_min
f_max_external = 6.5e9 - f_max
df_external = f_max - f_min
freqs_external = np.arange(f_min_external, f_max_external + 0.1, df_external)
frequency = np.array(
    np.concatenate(
        [frequencies + freqs_external[i] for i in range(len(freqs_external))]
    )
)
IFs = [
    frequencies[len(frequencies) // 4],
    frequencies[len(frequencies) // 2],
    frequencies[3*len(frequencies) // 4],
]

c00 = []
c01 = []
c10 = []
c11 = []
for lo in freqs_external:
    for i in IFs:
        param = get_calibration_parameters("", config, "qubit", lo, i, 0)
        c00.append(param["correction_matrix"][0])
        c01.append(param["correction_matrix"][1])
        c10.append(param["correction_matrix"][2])
        c11.append(param["correction_matrix"][3])

with program() as qubit_spec:
    n = declare(int)  # QUA variable for the averaging loop
    i = declare(int)  # QUA variable for the LO frequency sweep
    f = declare(int)  # QUA variable for the qubit frequency
    I = declare(fixed)  # QUA variable for the measured 'I' quadrature
    Q = declare(fixed)  # QUA variable for the measured 'Q' quadrature
    I_st = declare_stream()  # Stream for the 'I' quadrature
    Q_st = declare_stream()  # Stream for the 'Q' quadrature
    n_st = declare_stream()  # Stream for the averaging iteration 'n'

    c00_qua = declare(fixed, value=c00)  # QUA variable for the measured 'I' quadrature
    c01_qua = declare(fixed, value=c01)  # QUA variable for the measured 'I' quadrature
    c10_qua = declare(fixed, value=c10)  # QUA variable for the measured 'I' quadrature
    c11_qua = declare(fixed, value=c11)  # QUA variable for the measured 'I' quadrature
    count = declare(int, value=0)  # QUA variable for the qubit frequency


    with for_(i, 0, i < len(freqs_external) + 1, i + 1):
        pause()  # This waits until it is resumed from python
        with for_(n, 0, n < n_avg, n + 1):
            with for_(*from_array(f, frequencies)):
                # Update the frequency of the digital oscillator linked to the qubit element
                update_frequency("qubit", f)
                update_frequency("resonator", resonator_IF)
                with switch_(f):
                    for idx, current_if in enumerate(IFs):
                        with case_(int(current_if)):
                            update_frequency("resonator", 0)
                            update_correction("qubit", c00_qua[len(IFs)*i+idx], c01_qua[len(IFs)*i+idx], c10_qua[len(IFs)*i+idx], c11_qua[len(IFs)*i+idx])
                # Play the saturation pulse to put the qubit in a mixed state
                play("saturation", "qubit")
                # Align the two elements to measure after playing the qubit pulse.
                # One can also measure the resonator while driving the qubit (2-tone spectroscopy) by commenting the 'align'
                align("qubit", "resonator")
                # Measure the state of the resonator
                measure(
                    "readout",
                    "resonator",
                    None,
                    dual_demod.full("cos", "out1", "sin", "out2", I),
                    dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
                )
                # Wait for the qubit to decay to the ground state
                wait(thermalization_time * u.ns, "resonator")
                # Save the 'I' & 'Q' quadratures to their respective streams
                save(I, I_st)
                save(Q, Q_st)
        # Save the LO iteration to get the progress bar
        save(i, n_st)

    with stream_processing():
        # Cast the data into a 2D matrix, average the matrix along its second dimension (of size 'n_avg') and store the results
        # (1D vector) on the OPX processor
        I_st.buffer(len(frequencies)).buffer(n_avg).map(FUNCTIONS.average()).save_all(
            "I"
        )
        Q_st.buffer(len(frequencies)).buffer(n_avg).map(FUNCTIONS.average()).save_all(
            "Q"
        )
        n_st.save_all("iteration")

#####################################
#  Open Communication with the QOP  #
#####################################
qmm = QuantumMachinesManager(
    host=qop_ip, port=qop_port, cluster_name=cluster_name, octave=octave_config
)



def calibrate_several_LOs(element, lo_frequencies, central_if_frequency):
    """Calibrate a given element for a list of LO frequencies and a single intermediate frequency.

    :param element: An element connected to the Octave.
    :param lo_frequencies: List of LO frequencies to calibrate.
    :param central_if_frequency: Intermediate frequency use to perform the calibration.
    """
    for lo in lo_frequencies:
        print(f"Calibrate (LO, IF) = ({lo/u.MHz}, {central_if_frequency/u.MHz}) MHz")
        qm.calibrate_element(element, {lo: (central_if_frequency,)})


###############
# Run Program #
###############
# Open the quantum machine
qm = qmm.open_qm(config)

# Calibrate the element for each LO frequency of the sweep and the central intermediate frequency

calibrate = False
if calibrate:
    for lo in freqs_external:
        qm.calibrate_element("qubit", {lo: IFs})

# Send the QUA program to the OPX, which compiles and executes it. It will stop at the 'pause' statement.
job = qm.execute(qubit_spec)
# Creates results handles to fetch the data
res_handles = job.result_handles
I_handle = res_handles.get("I")
Q_handle = res_handles.get("Q")
n_handle = res_handles.get("iteration")
# Initialize empty vectors to store the global 'I' & 'Q' results
I_tot = []
Q_tot = []
# Live plotting
fig = plt.figure()
interrupt_on_close(fig, job)  # Interrupts the job when closing the figure
for i in range(len(freqs_external)):  # Loop over the LO frequencies
    # Set the frequency of the LO source
    qm.octave.set_lo_frequency("qubit", freqs_external[i])
    print(job.get_element_correction("qubit"))
    set_correction_parameters(
        "", config, "qubit", freqs_external[i], IFs[0], 0, qm,
    )
    print(job.get_element_correction("qubit"))
    # qm.octave.set_element_parameters_from_calibration_db("qubit", job)

    # Resume the QUA program (escape the 'pause' statement)
    job.resume()
    # Wait until the program reaches the 'pause' statement again, indicating that the QUA program is done
    wait_until_job_is_paused(job)
    # Wait until the data of this run is processed by the stream processing
    I_handle.wait_for_values(i + 1)
    Q_handle.wait_for_values(i + 1)
    n_handle.wait_for_values(i + 1)
    # Fetch the data from the last OPX run corresponding to the current LO frequency
    I = np.concatenate(I_handle.fetch(i)["value"])
    Q = np.concatenate(Q_handle.fetch(i)["value"])
    iteration = n_handle.fetch(i)["value"][0]
    # Update the list of global results
    I_tot.append(I)
    Q_tot.append(Q)
    # Progress bar
    progress_counter(iteration, len(freqs_external))
    # Convert results into Volts
    S = u.demod2volts(I + 1j * Q, readout_len)
    R = np.abs(S)  # Amplitude
    phase = np.angle(S)  # Phase
    # Plot results
    plt.suptitle("Qubit spectroscopy")
    ax1 = plt.subplot(211)
    plt.plot((frequencies + freqs_external[i]) / u.MHz, R, ".")
    plt.xlabel("qubit frequency [MHz]")
    plt.ylabel(r"$\sqrt{I^2 + Q^2}$ [V]")
    plt.subplot(212, sharex=ax1)
    plt.plot((frequencies + freqs_external[i]) / u.MHz, phase, ".")
    plt.xlabel("qubit frequency [MHz]")
    plt.ylabel("Phase [rad]")
    plt.pause(0.1)
    plt.tight_layout()

# Interrupt the FPGA program
job.halt()
# Convert results into Volts
I = np.concatenate(I_tot)
Q = np.concatenate(Q_tot)
S = u.demod2volts(I + 1j * Q, readout_len)
R = np.abs(S)  # Amplitude
phase = np.angle(S)  # Phase
# Final plot
plt.figure()
plt.suptitle("Qubit spectroscopy")
ax1 = plt.subplot(211)
plt.plot(frequency / u.MHz, R, ".")
plt.xlabel("qubit frequency [MHz]")
plt.ylabel(r"$\sqrt{I^2 + Q^2}$ [V]")
plt.subplot(212, sharex=ax1)
plt.plot(frequency / u.MHz, phase, ".")
plt.xlabel("qubit frequency [MHz]")
plt.ylabel("Phase [rad]")
plt.pause(0.1)
plt.tight_layout()
