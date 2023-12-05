from matplotlib import pyplot as plt
from qm.qua import *
from qm import QuantumMachinesManager
from qualang_tools.plot import interrupt_on_close
from qualang_tools.results import fetching_tool
from configuration import *
import warnings

warnings.filterwarnings("ignore")
from videomode import VideoMode


def qua_prog(video_mode: VideoMode):
    with program() as prog:
        # Results variables
        single_shot_DC = declare(fixed)
        # Get the parameters from the video mode
        dc_offset = video_mode.declare_variables()
        # Streams
        signal_st = declare_stream()

        with infinite_loop_():
            # Update the parameters
            video_mode.load_parameters()
            # Update the dc_offset of the channel connected to the OPX analog input 1
            set_dc_offset("filter_cavity_1", "single", dc_offset)
            # Measure and integrate the signal received by the OPX
            measure(
                "readout",
                "detector_DC",
                None,
                integration.full("constant", single_shot_DC, "out1"),
            )
            # Save the measured value to its stream
            save(single_shot_DC, signal_st)
            # Wait between each iteration
            wait(1000)

        with stream_processing():
            signal_st.buffer(1000).save("signal")
    return prog


if __name__ == "__main__":
    # Open the Quantum Machine Manager
    qmm = QuantumMachinesManager(qop_ip, cluster_name="Cluster_83")
    # Open the Quantum Machine
    qm = qmm.open_qm(config)
    # Define the parameters to be updated in video mode with their initial value
    param_dict = {
        "dc_offset": 0.45,
    }
    # Initialize the video mode
    video_mode = VideoMode(qm, param_dict)
    # Get the QUA program
    prog = qua_prog(video_mode)
    # Execute the QUA program in video mode
    job = video_mode.execute(prog)
    # Get the results from the OPX in live mode
    results = fetching_tool(job, ["signal"], mode="live")
    # Live plotting
    fig = plt.figure()
    interrupt_on_close(fig, job)
    while results.is_processing():
        # Fetch data from the OPX
        signal = -results.fetch_all()[0] * 2**12 / readout_len
        # Plot the data
        plt.cla()
        plt.plot(signal, "-")
        plt.title("Error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.ylabel("Amplitude Error [arb. units]")
        plt.ylim((-0.5, 0.5))
        plt.pause(0.1)
