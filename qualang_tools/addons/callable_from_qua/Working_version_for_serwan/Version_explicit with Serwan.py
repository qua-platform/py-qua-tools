from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
import warnings
from qm import generate_qua_script

from callable_from_qua3 import program, run_local


warnings.filterwarnings("ignore")


@run_local
def set_lo_freq(q: str, qm, value):
    qm.set_output_dc_offset_by_element("AOM", "single", float(value) / 10)
    print(f"setting LO to {value} Hz to qubit {q}")


@run_local
def set_lo_power(q: str, qm, value):
    qm.set_output_dc_offset_by_element("AOM", "single", float(value) / 10)
    print(f"setting POWER to {value} Hz to qubit {q}")

# Open the quantum machine manager
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
# Open a quantum machine
qm = qmm.open_qm(config)
# Declare the Callable from QUA framework
# batches = CallableFromQUA()  # TODO Remove me
# Define your QUA program with the declare_all() and do_stream_processing() lines
with program() as prog:
    n = declare(int)
    n2 = declare(int)
    I = declare(fixed)
    I_st = declare_stream()
    # batches.declare_all()  # TODO: need batches declaration
    with for_(n2, 0, n2 < 2, n2 + 1):
        # set_lo_power(batches=batches, q="QUBIT", qm=qm, value=n2) # TODO: remove batches from here?
        set_lo_power(q="QUBIT", qm=qm, value=n2)
        with for_(n, 0, n < 3, n + 1):
            # set_lo_freq(batches=batches, q="AOM", qm=qm, value=n)  # TODO remove batches from here
            set_lo_freq(q="AOM", qm=qm, value=n)
            play("cw", "AOM")
            measure(
                "readout",
                "photo-diode",
                None,
                integration.full("constant", I, "out1"),
            )
            save(I, I_st)

    with stream_processing():
        I_st.save_all("I")
    # batches.do_stream_processing()  # TODO: need batches stream processing
# Execute the QUA program using the callable from QUA framework
%matplotlib qt
fig = plt.figure()
def live_plot(res_handles):
    data = res_handles.get("I").fetch_all()["value"]
    # print(data)
    plt.cla()
    plt.plot(data, "ko")
    plt.pause(0.01)

with prog.local_run(qm, funcs=[live_plot]):
    job = qm.execute(prog)

# job = batches.execute(qm, prog)  # TODO Make this unnecessary

print(generate_qua_script(prog, config)[:1000])
