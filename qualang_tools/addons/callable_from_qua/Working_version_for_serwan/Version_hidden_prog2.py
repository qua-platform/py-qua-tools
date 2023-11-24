from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
import warnings
from callable_from_qua_buildprog2 import CallableFromQUA, run_local

warnings.filterwarnings("ignore")


# Define your local functions to be executed in Python but called from your QUA program
@run_local
def set_lo_freq(q: str, qm, value):
    qm.set_output_dc_offset_by_element("AOM", "single", float(value) / 10)
    print(f"setting LO to {value} Hz to {q}")


@run_local
def set_lo_power(q: str, qm, value):
    qm.set_output_dc_offset_by_element("AOM", "single", float(value) / 10)
    print(f"setting POWER to {value} Hz to {q}")


# Define your QUA program in a function and without the program() scope
def my_prog(callables_from_qua, qm):
    with program() as prog:
        n = declare(int)
        n2 = declare(int)
        I = declare(fixed)
        I_st = declare_stream()
        with for_(n2, 0, n2 < 2, n2 + 1):
            set_lo_power(batches=callables_from_qua, q="QUBIT", qm=qm, value=n2)  # TODO: could we get rid of batches=??
            with for_(n, 0, n < 3, n + 1):
                set_lo_freq(batches=callables_from_qua, q="AOM", qm=qm, value=n)
                play("cw", "AOM")
                measure(
                    "readout", "photo-diode", None, integration.full("constant", I, "out1")
                )
                save(I, I_st)

        with stream_processing():
            I_st.save_all("I")
    return prog

# Open the quantum machine manager
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
# Open a quantum machine
qm = qmm.open_qm(config)
# Declare the Callable from QUA framework
batches = CallableFromQUA(my_prog, qm)
# Execute the QUA program using the callable from QUA framework
job = batches.execute()

print(batches.generate_qua_script(config))
print(-job.result_handles.get("I").fetch_all()["value"] * 2**12 / readout_len)
