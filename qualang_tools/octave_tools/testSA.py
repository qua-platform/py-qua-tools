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
from qualang_tools.octave_tools import (
    get_calibration_parameters,
    set_correction_parameters,
)
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
# config["elements"]["qubit"]["intermediate_frequency"] = frequencies[
#     len(frequencies) // 2
# ]

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
    frequencies[3 * len(frequencies) // 4],
]

c00 = []
c01 = []
c10 = []
c11 = []

param = get_calibration_parameters("", config, "qubit", 5e9, 50e6, 0)
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

    # pause()  # This waits until it is resumed from python
    # Update the frequency of the digital oscillator linked to the qubit element
    # update_frequency("qubit", 50e6)
    # update_correction("qubit", c00_qua[0], c01_qua[0], c10_qua[0], c11_qua[0])
    # Play the saturation pulse to put the qubit in a mixed state
    with infinite_loop_():
        play("saturation", "qubit")


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
# set_correction_parameters(
#         "", config, "qubit", 5e9, 50e6, 0, qm, verbose_level=1
#     )
# Creates results handles to fetch the data
