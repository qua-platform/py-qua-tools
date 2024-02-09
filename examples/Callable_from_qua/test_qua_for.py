from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from configuration import *

from qualang_tools.callable_from_qua import *

patch_qua_program_addons()
enable_callable_from_qua()


# Define your callable_from_qua functions
@callable_from_qua
def set_lo_freq(q: str, qm, value):
    qm.set_output_dc_offset_by_element("AOM", "single", float(value) / 10)
    print(f"setting LO to {value} Hz to qubit {q}")


@callable_from_qua
def set_lo_power(q: str, qm, value):
    qm.set_output_dc_offset_by_element("AOM", "single", float(value) / 10)
    print(f"setting POWER to {value} Hz to qubit {q}")


# Open the quantum machine manager
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
# Open a quantum machine
qm = qmm.open_qm(config)
# Define your QUA program with the callable_from_qua functions
with program() as prog:
    n = declare(int)
    n2 = declare(int)
    I = declare(fixed)
    I_st = declare_stream()
    with for_(n2, 0, n2 < 2, n2 + 1):
        set_lo_power(q="QUBIT", qm=qm, value=n2)
        with for_(n, 0, n < 3, n + 1):
            set_lo_freq(q="AOM", qm=qm, value=n)
            measure(
                "readout",
                "readout_element",
                None,
                integration.full("constant", I, "out1"),
            )
            save(I, I_st)

    with stream_processing():
        I_st.save_all("I")

# Execute the QUA program using the callable from QUA framework
with prog.local_run(qm):
    job = qm.execute(prog)
