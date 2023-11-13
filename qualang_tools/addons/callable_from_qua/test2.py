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
    freq = qm.get_io1_value()["int_value"]
    print(f"setting LO to {freq} Hz to qubit {q}")

@run_local
def set_lo_power(q: str, qm):
    pow = qm.get_io2_value()["int_value"]
    print(f"setting POWER to {pow} Hz to qubit {q}")

def my_prog(callables_from_qua, qm):
    with program() as prog:
        n = declare(int)
        n2 = declare(int)
        with for_(n2, 0, n2 < 10, n2 + 1):
            assign(IO2, n2)
            set_lo_power(batches=callables_from_qua, q="QUBIT", qm=qm)
            with for_(n, 0, n<3, n+1):
                assign(IO1, n)
                set_lo_freq(batches=callables_from_qua, q="AOM", qm=qm)
                play("cw", "AOM")
    return prog

batches = CallableFromQUA()
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)
prog = my_prog(batches, qm)

job = batches.execute(qm, prog)

print(generate_qua_script(prog, config)[:1000])
