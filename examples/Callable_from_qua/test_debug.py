from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager

from configuration import *
from qualang_tools.callable_from_qua import *

patch_callable_from_qua()
enable_callable_from_qua()


# Define your callable_from_qua functions
@callable_from_qua
def qua_print(*args):
    text = ""
    for i in range(0, len(args) - 1, 2):
        text += f"{args[i]} = {args[i+1]} | "
    print(text)


#####################################
#  Open Communication with the QOP  #
#####################################
# Open the quantum machine manager
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
# from qm.simulate.credentials import create_credentials
# from qm.QuantumMachinesManager import QuantumMachinesManager
#
# qmm = QuantumMachinesManager(
#     host="serwan-dd85ae55.dev.quantum-machines.co",
#     port=443,
#     credentials=create_credentials(),
# )
# Open a quantum machine
qm = qmm.open_qm(config)


###################
# The QUA program #
###################
# Define your QUA program with the callable_from_qua functions
with program() as prog:
    n1 = declare(int)
    n2 = declare(int)
    I = declare(fixed)
    I_st = declare_stream()
    with for_(n1, 0, n1 < 2, n1 + 1):
        with for_(n2, 0, n2 < 3, n2 + 1):
            measure(
                "readout",
                "resonator",
                None,
                integration.full("cos", I, "out1"),
            )
            save(I, I_st)
            qua_print("n1", n1, "n2", n2, "I", I)

    with stream_processing():
        I_st.save_all("I")

# Execute the QUA program using the local_run context manager
job = qm.execute(prog)
