from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from configuration import *
import matplotlib.pyplot as plt
import warnings
import time
warnings.filterwarnings("ignore")


# %% Qua program


with program() as prog:
    n = declare(int)
    with for_(n, 0, n<10, n+1):
        assign(IO1, n)
        pause()
        play("cw", "AOM")

qmm = QuantumMachinesManager(host="192.168.0.129", cluster_name="Cluster_Bordeaux")
qm = qmm.open_qm(config)
job = qm.execute(prog)

for i in range(10):
    freq = qm.get_io1_value()["int_value"]
    print(f"setting LO to {freq} Hz to qubit AOM")
    time.sleep(1)
    job.resume()
