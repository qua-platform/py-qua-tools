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
res = []
@run_local
def qua_print(*args):
    # print(args)
    print(f"{args[0]}: {args[1]:.2e}, {args[2]}: {args[3]}")
    res.append(args[1])

def my_prog(callables_from_qua):  # TODO: no program() scope
    a = declare(fixed)
    I = declare(fixed)
    I_st = declare_stream()
    with for_(a, -1, a < 1, a + 0.5):
        play("cw"*amp(a), "AOM")
        measure(
            "readout", "photo-diode", None, integration.full("constant", I, "out1")
        )
        save(I, I_st)
        qua_print(callables_from_qua, "I", I, "a", a)

    with stream_processing():
        I_st.save_all("I")


def build_prog(callables_from_qua, sequence):  # TODO: behind the scene
    with program() as prog:
        callables_from_qua.declare_all()
        sequence(callables_from_qua)
        callables_from_qua.do_stream_processing()
    return prog


batches = CallableFromQUA()
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)
prog = build_prog(batches, my_prog)
job = batches.execute(qm, prog)

print(generate_qua_script(prog, config)[:1000])
print(-job.result_handles.get("I").fetch_all()["value"] * 2**12 / readout_len)
