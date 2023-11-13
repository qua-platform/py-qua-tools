import time

from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
from qm import generate_qua_script
from configuration import *
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings("ignore")

from callable_from_qua2 import CallableFromQUA, run_local

# %% Qua program

@run_local
def update_offset(channel: str, qm):
    offset = qm.get_io1_value()["fixed_value"]
    print(f"Set DC offset of channel {channel} to {offset} V")
    # Can be QDAC or whatever
    qm.set_output_dc_offset_by_element(channel, "single", offset)
    time.sleep(0.5)


def my_prog(callables_from_qua, qm):
    with program() as prog:
        n = declare(int)
        n2 = declare(int)
        I = declare(fixed)
        correction = declare(fixed)
        corr_st = declare_stream()
        # with infinite_loop_():
        with for_(n2, 0, n2 < 20, n2 + 1):
            assign(correction, 0)
            with for_(n, 0, n<2**8, n+1):
                measure("readout", "photo-diode", None, integration.full("constant", I, "out1"))
                assign(correction, correction + (I>>8))
            assign(IO1, correction)  # Whatever processing
            update_offset(batches=callables_from_qua, channel="AOM", qm=qm)
            save(correction, corr_st)
        with stream_processing():
            corr_st.save_all("correction")
    return prog

batches = CallableFromQUA()
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)

def live_plot(res_handles):
    data = res_handles.get("correction").fetch_all()["value"]
    # print(data)
    plt.cla()
    plt.plot(data,'ko')
    plt.pause(0.01)

prog = my_prog(batches, qm)
job = batches.execute(qm, prog, live_plot)

print(generate_qua_script(prog, config)[:1000])

