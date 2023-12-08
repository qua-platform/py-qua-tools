from qm.qua import *
from qm.QuantumMachinesManager import QuantumMachinesManager
import matplotlib.pyplot as plt
from time import sleep

from qualang_tools.callable_from_qua import program, callable_from_qua
from configuration import *


@callable_from_qua
def update_offset(QM, channel: str, signal: float):
    target = 0.05  # Target voltage in V
    signal = -signal * 2**12 / readout_len
    correction = target - signal  # Correction to apply
    print(f"Set DC offset of channel {channel} to {correction} V (signal = {signal})")
    # Can be QDAC or whatever
    QM.set_output_dc_offset_by_element(channel, "single", correction)
    sleep(0.5)


qmm = QuantumMachinesManager(host="172.16.33.101", cluster_name="Cluster_83")
qm = qmm.open_qm(config)


with program() as prog:
    n = declare(int)
    n2 = declare(int)
    I = declare(fixed)
    signal = declare(fixed)
    signal_st = declare_stream()
    with for_(n2, 0, n2 < 20, n2 + 1):
        assign(signal, 0)
        with for_(n, 0, n < 2**8, n + 1):
            measure("readout", "resonator", None, integration.full("cos", I, "out1"))
            assign(signal, signal + (I >> 8))
        update_offset(QM=qm, channel="flux_line", signal=signal)
        save(signal, signal_st)
    with stream_processing():
        signal_st.save_all("signal")


def live_plot(res_handles):
    data = -res_handles.get("signal").fetch_all()["value"] * 2**12 / readout_len
    plt.cla()
    plt.plot(data, "ko")
    plt.pause(0.01)


# Execute the QUA program using the local_run context manager
with prog.local_run(qm, [live_plot]):
    job = qm.execute(prog)
