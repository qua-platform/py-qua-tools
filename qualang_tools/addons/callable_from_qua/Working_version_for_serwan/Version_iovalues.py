from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
import warnings
from qm import generate_qua_script

warnings.filterwarnings("ignore")

from callable_from_qua2 import CallableFromQUA, run_local

# %% Qua program


@run_local
def set_lo_freq(q: str, qm):
    freq = qm.get_io1_value()["int_value"]  # TODO need iovalues
    qm.set_output_dc_offset_by_element("AOM", "single", float(freq) / 10)
    print(f"setting LO to {freq} Hz to qubit {q}")


@run_local
def set_lo_power(q: str, qm):
    pow = qm.get_io2_value()["int_value"]  # TODO need iovalues
    qm.set_output_dc_offset_by_element("AOM", "single", float(pow) / 10)
    print(f"setting POWER to {pow} Hz to qubit {q}")


def my_prog(callables_from_qua, qm):
    with program() as prog:
        n = declare(int)
        n2 = declare(int)
        I = declare(fixed)
        I_st = declare_stream()
        with for_(n2, 0, n2 < 2, n2 + 1):
            assign(IO2, n2)  # TODO need iovalues
            set_lo_power(batches=callables_from_qua, q="QUBIT", qm=qm)
            with for_(n, 0, n < 3, n + 1):
                assign(IO1, n)  # TODO need iovalues
                set_lo_freq(batches=callables_from_qua, q="AOM", qm=qm)
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
    return prog


batches = CallableFromQUA()
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)
prog = my_prog(batches, qm)
job = batches.execute(qm, prog)

print(generate_qua_script(prog, config)[:1000])
print(-job.result_handles.get("I").fetch_all()["value"] * 2**12 / readout_len)
