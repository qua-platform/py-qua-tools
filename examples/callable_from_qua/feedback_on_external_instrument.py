from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from time import sleep
from configuration import *
from qualang_tools.callable_from_qua import *


# Patch to add the callable from qua functions to the main SDK
patch_qua_program_addons()


@callable_from_qua
def update_offset(QM, element, signal):
    target = 0.05  # Target voltage in V
    signal = -signal * 2**12 / 1000  # Measured signal in V
    correction = target - signal  # Correction to apply
    print(f"Set DC offset of element {element} to {correction:.4f} V (signal = {signal:.4f} V)")
    # Can be QDAC or another voltage source
    QM.set_output_dc_offset_by_element(element, "I", correction)
    sleep(0.5)


#####################################
#  Open Communication with the QOP  #
#####################################
# Open the quantum machine manager
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
# Open a quantum machine
qm = qmm.open_qm(config)

###################
# The QUA program #
###################
# Define your QUA program with the callable_from_qua functions
with program() as prog:
    n = declare(int)
    n2 = declare(int)
    I = declare(fixed)
    signal = declare(fixed)
    signal_st = declare_stream()
    with for_(n2, 0, n2 < 20, n2 + 1):
        # Measure and average 256 times
        assign(signal, 0)
        with for_(n, 0, n < 2**8, n + 1):
            measure("readout", "qe1", None, integration.full("cos", I, "out1"))
            assign(signal, signal + (I >> 8))
        # Update a voltage level based on the averaged measured signal
        update_offset(QM=qm, element="qe1", signal=signal)
        save(signal, signal_st)

    with stream_processing():
        signal_st.save_all("signal")

# Execute the QUA program
job = qm.execute(prog)
