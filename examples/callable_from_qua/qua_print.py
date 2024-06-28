from qm.qua import *
from qm import QuantumMachinesManager
from configuration import *
from qualang_tools.callable_from_qua import callable_from_qua, patch_qua_program_addons

# Patch to add the callable from qua functions to the main SDK
patch_qua_program_addons()

# Define your callable_from_qua functions
@callable_from_qua
def qua_print(*args):
    text = ""
    for i in range(0, len(args) - 1, 2):
        text += f"{args[i]} = {args[i+1]} | "
    print(text)


###################
# The QUA program #
###################
# Define your QUA program with the callable_from_qua functions
with program() as prog:
    n1 = declare(int)
    n2 = declare(int)
    I = declare(fixed)
    I10 = declare(fixed)
    I_st = declare_stream()
    with for_(n1, 0, n1 < 2, n1 + 1):
        with for_(n2, 0, n2 < 3, n2 + 1):
            measure(
                "readout",
                "qe1",
                None,
                integration.full("cos", I, "out1"),
            )
            save(I, I_st)
            assign(I10, Cast.mul_fixed_by_int(I, 10))
            # Print the value of some variables in the Python terminal
            qua_print("n1", n1, "n2", n2, "I", I, "I*10", I10)

    with stream_processing():
        I_st.save_all("I")

#####################################
#  Open Communication with the QOP  #
#####################################
# Open the quantum machine manager
qmm = QuantumMachinesManager(host=qop_ip, cluster_name=cluster_name)
# Open a quantum machine
qm = qmm.open_qm(config)
# Execute the QUA program
job = qm.execute(prog)
