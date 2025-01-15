from qm.qua import *
from qm import QuantumMachinesManager
from configuration import *
from qualang_tools.callable_from_qua import *
from qualang_tools.loops import from_array
import numpy as np


# Patch to add the callable from qua functions to the main SDK
patch_qua_program_addons()


# Define your callable_from_qua functions
# Note that this framework can be easily adapted to update parameters from other instruments using their dedicated API
@callable_from_qua
def set_I_offset(q: str, QM, value):
    QM.set_output_dc_offset_by_element(q, "I", value)
    print(f"setting the I offset of element {q} to {value} V ")


@callable_from_qua
def set_Q_offset(q: str, QM, value):
    QM.set_output_dc_offset_by_element(q, "Q", value)
    print(f"setting the Q offset of element {q} to {value} V ")


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
    I_offset = declare(fixed)
    Q_offset = declare(fixed)
    I = declare(fixed)
    I_st = declare_stream()
    with for_(*from_array(Q_offset, np.linspace(0, 0.5, 5))):
        # Update a first external parameter directly from a QUA for loop
        set_Q_offset(q="qe1", QM=qm, value=Q_offset)
        with for_(*from_array(I_offset, np.linspace(-0.5, 0.5, 5))):
            # Update a second external parameter directly from a QUA for loop
            set_I_offset(q="qe1", QM=qm, value=I_offset)
            measure(
                "readout",
                "qe1",
                None,
                integration.full("cos", I, "out1"),
            )
            save(I, I_st)

    with stream_processing():
        I_st.save_all("I")

# Execute the QUA program
job = qm.execute(prog)
