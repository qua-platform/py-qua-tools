import time

from matplotlib import pyplot as plt
from qm.qua import *
from qm import QuantumMachinesManager
from qualang_tools.addons.variables import assign_variables_to_element
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import fetching_tool
from configuration import *
import warnings

warnings.filterwarnings("ignore")
from videomode import VideoMode


def PID_prog(video_mode: VideoMode):
    with program() as prog:
        # Results variables
        single_shot_DC = declare(fixed)
        # PID variables
        video_mode.declare_variables()
        signal_st = declare_stream()


        with infinite_loop_():
            # Update the PID parameters based on the user input.
            dc_offset_1 = video_mode.__getitem__("dc_offset")

            video_mode.load_parameters()
            # Measure and integrate the signal received by the detector --> DC measurement
            measure(
                "readout",
                "detector_DC",
                None,
                integration.full("constant", single_shot_DC, "out1"),
            )


            set_dc_offset("filter_cavity_1", "single", dc_offset_1)
            save(single_shot_DC, signal_st)

            # Wait between each iteration
            wait(1000)

        with stream_processing():
            signal_st.buffer(1000).save("signal")
    return prog


if __name__ == "__main__":
    qmm = QuantumMachinesManager(qop_ip, cluster_name="Cluster_83")
    qm = qmm.open_qm(config)

    param_dict = {
        "dc_offset": 0.0,
    }

    video_mode = VideoMode(qm, param_dict)
    prog = PID_prog(video_mode)
    job = video_mode.execute(prog)
    results = fetching_tool(job, ["signal"], mode="live")
    fig = plt.figure()
    interrupt_on_close(fig, job)

    while results.is_processing():
        signal = -results.fetch_all()[0]*2**12/readout_len

        plt.cla()
        plt.plot(signal, "-")
        plt.title("Error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.ylabel("Amplitude Error [arb. units]")
        plt.ylim((-0.5, 0.5))
        plt.pause(0.1)
