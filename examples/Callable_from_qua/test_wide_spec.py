from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from configuration_octave import *
import matplotlib.pyplot as plt
import warnings
from qualang_tools.loops import from_array
from qualang_tools.callable_from_qua import *

patch_qua_program_addons()
enable_callable_from_qua()


warnings.filterwarnings("ignore")


####################
# Helper functions #
####################
def get_LOs(f_start: float, f_end: float, intermediate_frequencies=()):
    """Get the set of LO frequencies for a given range and IF sweep.

    :param f_start: First frequency of the scan in Hz.
    :param f_end: Last frequency of the scan in Hz.
    :param intermediate_frequencies: List of the intermediate frequencies used in the sweep in Hz.
    :return: The list of LO frequencies and the total frequency axis.
    """
    first_LO = f_start - intermediate_frequencies[0]
    last_LO = f_end - intermediate_frequencies[-1]
    step_LO = intermediate_frequencies[-1] - intermediate_frequencies[0]

    LO_frequencies = np.arange(first_LO, last_LO + 0.1, step_LO)
    f_total = np.concatenate([LO + intermediate_frequencies for LO in LO_frequencies])
    return LO_frequencies, f_total


# Calibrate all LOs
def calibrate_several_LOs(element, lo_frequencies, central_if_frequency):
    """Calibrate a given element for a list of LO frequencies and a single intermediate frequency.

    :param element: An element connected to the Octave.
    :param lo_frequencies: List of LO frequencies to calibrate.
    :param central_if_frequency: Intermediate frequency use to perform the calibration.
    """
    for lo in lo_frequencies:
        print(f"Calibrate (LO, IF) = ({lo/u.MHz}, {central_if_frequency/u.MHz}) MHz")
        qm.calibrate_element(element, {lo: (central_if_frequency,)})


@callable_from_qua
def set_lo_freq(QM, lo_freq_kHz):
    lo_freq_Hz = lo_freq_kHz * u.kHz
    print(f"setting LO to {lo_freq_Hz / u.GHz} GHz")
    QM.octave.set_lo_frequency("qubit", lo_freq_Hz)
    QM.octave.set_element_parameters_from_calibration_db("qubit", QM.get_running_job())


#####################################
#  Open Communication with the QOP  #
#####################################
# Open the quantum machine manager
qmm = QuantumMachinesManager(qop_ip, cluster_name=cluster_name, octave=octave_config)
# Open the quantum machine
qm = qmm.open_qm(config)

###################
# The QUA program #
###################
IFs = np.linspace(1e6, 251e6, 101)
LOs, f_axis = get_LOs(4.501e9, 6.75e9, IFs)
config["elements"]["qubit"]["intermediate_frequency"] = IFs[len(IFs) // 2]

with program() as prog:
    n_avg = 100
    n = declare(int)
    f_LO = declare(int)
    f_IF = declare(int)
    I = declare(fixed)
    Q = declare(fixed)
    I_st = declare_stream()
    Q_st = declare_stream()
    # Loop over the LO frequencies in kHz
    with for_(*from_array(f_LO, LOs / u.kHz)):
        # Update the LO frequency in Python
        set_lo_freq(QM=qm, lo_freq_kHz=f_LO)
        # Averaging loop
        with for_(n, 0, n < n_avg, n + 1):
            # Loop over the intermediate frequencies
            with for_(*from_array(f_IF, IFs)):
                # Update the qubit frequency
                update_frequency("qubit", f_IF)
                # Drive the qubit to a mixed state
                play("cw", "qubit")
                # Measure the readout resonator
                measure(
                    "readout",
                    "resonator",
                    None,
                    dual_demod.full("cos", "out1", "sin", "out2", I),
                    dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
                )
                # Wait for the qubit to decay to the ground state
                wait(1000, "resonator")
                # Save the 'I' & 'Q' quadratures to their respective streams
                save(I, I_st)
                save(Q, Q_st)

    with stream_processing():
        # Stream all the data at the end of the program
        # I_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).buffer(len(LOs)).save("I")
        # Q_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).buffer(len(LOs)).save("Q")
        # Stream the data for each LO, needed for live plotting
        I_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).save_all("I")
        Q_st.buffer(len(IFs)).buffer(n_avg).map(FUNCTIONS.average()).save_all("Q")


# Calibrate the element for each LO frequency of the sweep and the central intermediate frequency
calibrate = False
if calibrate:
    calibrate_several_LOs("qubit", LOs, IFs[len(IFs) // 2])


def live_plot(res_handles):
    count = res_handles.get("I").count_so_far()
    if count > 0:
        I = res_handles.get("I").fetch_all()["value"][count - 1]
        Q = res_handles.get("Q").fetch_all()["value"][count - 1]
        S = u.demod2volts(I + 1j * Q, readout_len)
        R = np.abs(S)
        phase = np.angle(S)
        plt.subplot(211)
        plt.plot((LOs[count - 1] + IFs) / u.MHz, R)
        plt.ylabel(r"$R=\sqrt{I^2 + Q^2}$ [V]")
        plt.xlabel("Frequency [MHz]")
        plt.subplot(212)
        plt.plot((LOs[count - 1] + IFs) / u.MHz, phase)
        plt.ylabel("Phase [rad]")
        plt.xlabel("Frequency [MHz]")
        plt.tight_layout()
        plt.pause(0.01)


# Execute the QUA program using the local_run context manager
with prog.local_run(qm, [live_plot]):
    fig = plt.figure()
    job = qm.execute(prog)

# Fetch and plot all the data at the end
I = np.concatenate(job.result_handles.get("I").fetch_all()["value"])
Q = np.concatenate(job.result_handles.get("Q").fetch_all()["value"])
S = u.demod2volts(I + 1j * Q, readout_len)
R = np.abs(S)
phase = np.angle(S)
plt.figure()
plt.subplot(211)
plt.plot(f_axis / u.MHz, R)
plt.ylabel(r"$R=\sqrt{I^2 + Q^2}$ [V]")
plt.xlabel("Frequency [MHz]")
plt.subplot(212)
plt.plot(f_axis / u.MHz, phase)
plt.ylabel("Phase [rad]")
plt.xlabel("Frequency [MHz]")
plt.tight_layout()
