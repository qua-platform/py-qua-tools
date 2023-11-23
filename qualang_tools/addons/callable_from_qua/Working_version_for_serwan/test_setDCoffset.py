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
def set_dc_offset(channel: str, offset: float, qm):
    print(f"Set DC offset of channel {channel} to {offset} V")
    # Can be QDAC or whatever
    qm.set_output_dc_offset_by_element(channel, "single", offset)


# def my_prog(callables_from_qua, qm):
#     with program() as prog:
#         n = declare(int)
#         callables_from_qua.declare_all()
#         for v in [0.1, 0.2, 0.3]:
#             set_dc_offset(batches=callables_from_qua, channel="AOM", offset=v, qm=qm)
#             with for_(n, 0, n<3, n+1):
#                 play("cw", "AOM")
#
#         with stream_processing():
#             callables_from_qua.do_stream_processing()
#     return prog
#
# batches = CallableFromQUA()
# qmm = QuantumMachinesManager(host="192.168.0.129", cluster_name="Cluster_Bordeaux")
# qm = qmm.open_qm(config)
#
# prog = my_prog(batches, qm)
# job = batches.execute(qm, prog)

qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)
batches = CallableFromQUA()

with program() as prog:
    n = declare(int)
    I = declare(fixed)
    I_st = declare_stream()
    for v in [-0.1, 0.2, -0.3]:
        set_dc_offset(batches=batches, channel="AOM", offset=v, qm=qm)
        # set_dc_offset(batches=batches, channel="photo-diode", offset=-0.1*v, qm=qm)
        with for_(n, 0, n < 3, n + 1):
            play("cw" * amp(0), "AOM")
        measure("readout", "photo-diode", None, integration.full("constant", I, "out1"))
        save(I, I_st)

    with stream_processing():
        I_st.save_all("I")
job = batches.execute(qm, prog)

print(generate_qua_script(prog, config)[:1100])
print(-job.result_handles.get("I").fetch_all()["value"] * 2**12 / readout_len)
