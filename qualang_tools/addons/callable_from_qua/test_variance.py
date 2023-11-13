import time

from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
from qm import SimulationConfig
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

len_span_freq_biases = 2
len_sweep_vgs_x_biases = 3
len_sweep_vgs_y_biases = 4
opx_n_avg = 5
len_rf_Vp_biases = 6

with program() as prog:
    n = declare(int)
    n1 = declare(int)
    n2 = declare(int)
    n3 = declare(int)
    n4 = declare(int)
    I = declare(int)
    I_st = [declare_stream()]
    k = 0
    # with infinite_loop_():
    with for_(n, 0, n < len_span_freq_biases, n + 1):
        with for_(n1, 0, n1 < opx_n_avg, n1 + 1):
            with for_(n2, 0, n2 < len_sweep_vgs_y_biases, n2 + 1):
                with for_(n3, 0, n3 < len_sweep_vgs_x_biases, n3 + 1):
                    with for_(n4, 0, n4 < len_span_freq_biases, n4+1):
                        assign(I, n+n1+n2+n3+n4)
                        save(I, I_st[0])
                        wait(1000)
    with stream_processing():
        ((I_st[k].buffer(len_span_freq_biases).buffer(len_sweep_vgs_x_biases).buffer(len_sweep_vgs_y_biases) *
         I_st[k].buffer(len_span_freq_biases).buffer(len_sweep_vgs_x_biases).buffer(len_sweep_vgs_y_biases)
         ).buffer(opx_n_avg).map(FUNCTIONS.average()) -
         (I_st[k].buffer(len_span_freq_biases).buffer(len_sweep_vgs_x_biases).buffer(len_sweep_vgs_y_biases).buffer(opx_n_avg).map(FUNCTIONS.average()) *
         I_st[k].buffer(len_span_freq_biases).buffer(len_sweep_vgs_x_biases).buffer(len_sweep_vgs_y_biases).buffer(opx_n_avg).map(FUNCTIONS.average()))
         ).buffer(len_rf_Vp_biases).save_all(f"I_var{k}")

batches = CallableFromQUA()
qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)
job = qm.execute(prog)
job.result_handles.wait_for_all_values()
I_var = job.result_handles.get("I_var0").fetch_all()
print(I_var)




