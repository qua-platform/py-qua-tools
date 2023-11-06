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
with for_(n, 0, n < 10, n + 1):
    update_power(10)
    with for_(n, 0, n < 10, n + 1):
        # assign(IO1, n)
        update_frequency(100e6)
        pause()
        play("cw", "AOM")
assign(IO2, -1)

qmm = QuantumMachinesManager(host="192.168.0.129", cluster_name="Cluster_Bordeaux")
qm = qmm.open_qm(config)
job = qm.execute(prog)

for i in range(10):
    freq = qm.get_io1_value()["int_value"]
    print(f"setting LO to {freq} Hz to qubit AOM")
    time.sleep(1)
    job.resume()

run_qua_callables(job)


# QUA callables
def run_qua_callables(job):
    while not job.is_terminated:
        fn_idx = qm.get_io2_value()["int_value"]
        fn = prog.qua_callables[fn_idx]

        val = qm.get_io1_value()["int_value"]


fn(val)


def callable_from_qua(fn):
    prog = get_program()
    if not hasattr(prog, "qua_callables"):
        prog.qua_callables = []

func_idx = len(prog.qua_callables)
prog.qua_callables.append(fn)


def wrapper(val):
    qm.set_io2_value(func_idx)
    qm.set_io1_value(val)
    pause()
return wrapper


@callable_from_qua
def update_frequency(val):
    local_oscillator.frequency(val)

@callable_from_qua
def update_power(val):
    local_oscillator.power(val)