from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qualang_tools.loops import from_array

from qualang_tools.callable_from_qua import program, callable_from_qua
from configuration import *


# Define your callable_from_qua functions
@callable_from_qua
def update_from_python(qm, value, n):
    out = float(value * 10000)
    f = np.random.randint(1e6, 300e6)
    qm.get_running_job().insert_input_stream("frequency", f)
    qm.get_running_job().insert_input_stream("amplitude", out)
    print(f"Got {value}, sent {out} and {f}")


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
frequencies = np.arange(15, 250, 0.1) * u.MHz
# Define your QUA program with the callable_from_qua functions
with program() as prog:
    n = declare(int)
    f = declare(int)
    f_res = declare_input_stream(int, name="frequency")
    I = declare(fixed)
    Q = declare(fixed)
    a = declare_input_stream(fixed, name="amplitude")
    I_st = declare_stream()
    with for_(*from_array(f, frequencies)):
        # Update the qubit frequency
        update_frequency("resonator", f)
        # Measure the readout resonator
        measure(
            "readout",
            "resonator",
            None,
            dual_demod.full("cos", "out1", "sin", "out2", I),
            dual_demod.full("minus_sin", "out1", "cos", "out2", Q),
        )
        # Wait for the resonator to deplete
        wait(1000, "resonator")
        save(I, I_st)
        update_from_python(qm=qm, value=I, n=n)
        advance_input_stream(f)
        advance_input_stream(a)
        update_frequency("resonator", f)
        qua_print("a", a, "f", f)

    with stream_processing():
        I_st.save_all("I")

# Execute the QUA program using the local_run context manager
with prog.local_run(qm):
    job = qm.execute(prog)
