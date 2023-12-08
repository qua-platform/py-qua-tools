from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager

from qualang_tools.callable_from_qua import program, callable_from_qua
from configuration import *


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
with prog.local_run(qm):
    job = qm.execute(prog)
