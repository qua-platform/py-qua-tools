from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

from run_local import run_local
from callable_from_qua import BatchJob

# %% Qua program

@run_local
def set_lo_freq(q: str, qm):
    freq = qm.get_io1_value()["int_value"]
    print(f"setting LO to {freq} Hz to qubit {q}")

def my_prog(batches, qm):
    with program() as prog:
        n = declare(int)
        with for_(n, 0, n<10, n+1):
            assign(IO1, n)
            set_lo_freq(batches=batches, q="AOM", qm=qm)
            play("cw", "AOM")
    return prog

batches = BatchJob(10)
qmm = QuantumMachinesManager(host="192.168.0.129", cluster_name="Cluster_Bordeaux")
qm = qmm.open_qm(config)
prog = my_prog(batches, qm)
job = batches.execute(qm, prog)


