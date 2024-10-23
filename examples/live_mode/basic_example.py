from matplotlib import pyplot as plt
from qm.qua import *
from qm import QuantumMachinesManager
from qualang_tools.results import fetching_tool
from configuration import *
from qualang_tools.video_mode.livemode import LiveMode


def qua_prog(vm: LiveMode):
    with program() as prog:
        # Results variables
        single_shot_1 = declare(fixed)
        single_shot_2 = declare(fixed)
        # Get the parameters from the video mode
        dc_offset_1, dc_offset_2 = vm.declare_variables()
        # Streams
        signal1_st = declare_stream()
        signal2_st = declare_stream()

        with infinite_loop_():
            # Update the parameters
            vm.load_parameters()
            # Update the dc_offset of the channel connected to the OPX analog input 1
            set_dc_offset("filter_cavity_1", "single", dc_offset_1)
            set_dc_offset("filter_cavity_2", "single", dc_offset_2)
            # Measure and integrate the signal received by the OPX
            measure(
                "readout",
                "detector_DC",
                None,
                integration.full("constant", single_shot_1, "out1"),
                integration.full("constant", single_shot_2, "out2"),
            )
            # Save the measured value to its stream
            save(single_shot_1, signal1_st)
            save(single_shot_2, signal2_st)
            # Wait between each iteration
            wait(1000)

        with stream_processing():
            signal1_st.buffer(1000).save("signal1")
            signal2_st.buffer(1000).save("signal2")
    return prog


if __name__ == "__main__":
    # Open the Quantum Machine Manager
    qmm = QuantumMachinesManager(qop_ip, cluster_name=cluster_name)
    # Open the Quantum Machine
    qm = qmm.open_qm(config)
    # Define the parameters to be updated in video mode with their initial value and QUA type
    param_dict = {
        "dc_offset_1": (0.0, fixed),
        "dc_offset_2": (0.0, fixed),
    }
    # Initialize the video mode
    video_mode = LiveMode(qm, param_dict)
    # Get the QUA program
    qua_prog = qua_prog(video_mode)
    # Execute the QUA program in video mode
    job = video_mode.execute(qua_prog)
    # Get the results from the OPX in live mode
    results = fetching_tool(job, ["signal1", "signal2"], mode="live")
    # Live plotting
    fig = plt.figure()
    while results.is_processing():
        # Fetch data from the OPX
        signal1, signal2 = results.fetch_all()
        # Convert the data into Volt
        signal1 = -u.demod2volts(signal1, readout_len)
        signal2 = -u.demod2volts(signal2, readout_len)
        # Plot the data
        plt.cla()
        plt.plot(signal1, "b-")
        plt.plot(signal2, "r-")
        plt.title("Error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.ylabel("Amplitude Error [arb. units]")
        plt.ylim((-0.5, 0.5))
        plt.pause(0.1)
