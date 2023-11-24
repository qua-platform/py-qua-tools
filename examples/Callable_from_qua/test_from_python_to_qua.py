from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from callable_from_qua import program, run_local
from configuration import *

# Define your run_local functions
@run_local
def update_from_python(qm, value,n):
    out = value*100+0.1
    f = np.random.randint(1e6, 300e6)
    print(f"Got {value}, sent {out} and {f}")
    return out, f

@run_local
def qua_print(*args):
    text = ""
    for i in range(0, len(args)-1, 2):
        text += f"{args[i]} = {args[i+1]} | "
    print(text)


# Open the quantum machine manager
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
# Open a quantum machine
qm = qmm.open_qm(config)
# Define your QUA program with the run_local functions
with program() as prog:
    n = declare(int)
    f = declare(int)
    I = declare(fixed)
    a = declare(fixed)
    I_st = declare_stream()
    with for_(n, 0, n < 10, n + 1):
        measure(
            "readout"*amp(a),
            "resonator",
            None,
            integration.full("cos", I, "out1"),
        )
        save(I, I_st)
        update_from_python(qm=qm, value=I, n=n)
        assign(a, IO1)
        assign(f, IO2)
        update_frequency("resonator", f)
        qua_print("a", a, "f", f)

    with stream_processing():
        I_st.save_all("I")

# Execute the QUA program using the callable from QUA framework
with prog.local_run(qm):
    job = qm.execute(prog)
