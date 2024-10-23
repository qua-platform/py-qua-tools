from matplotlib import pyplot as plt
from qm.qua import *
from qm import QuantumMachinesManager
from qualang_tools.addons.variables import assign_variables_to_element
from qualang_tools.results import fetching_tool
from configuration import *
from qualang_tools.video_mode.livemode import LiveMode


####################
# Helper functions #
####################
def PID_derivation(input_signal, bitshift_scale_factor, gain_P, gain_I, gain_D, alpha, target):
    """

    :param input_signal: Result of the demodulation
    :param bitshift_scale_factor: Scale factor as 2**bitshift_scale_factor that multiplies the error signal to avoid resolution issues with QUA fixed (3.28)
    :param gain_P: Proportional gain.
    :param gain_I: Integral gain.
    :param gain_D: Derivative gain.
    :param alpha: Ratio between proportional and integral error: integrator_error = (1.0 - alpha) * integrator_error + alpha * error
    :param target: Setpoint to which the input signal should stabilize.
    :return: The total, proportional, integral and derivative errors.
    """
    error = declare(fixed)
    integrator_error = declare(fixed)
    derivative_error = declare(fixed)
    old_error = declare(fixed)

    # calculate the error
    assign(error, (target - input_signal) << bitshift_scale_factor)
    # calculate the integrator error with exponentially decreasing weights with coefficient alpha
    assign(integrator_error, (1.0 - alpha) * integrator_error + alpha * error)
    # calculate the derivative error
    assign(derivative_error, old_error - error)
    # save old error to be error
    assign(old_error, error)

    return (
        gain_P * error + gain_I * integrator_error + gain_D * derivative_error,
        error,
        integrator_error,
        derivative_error,
    )


###################
# The QUA program #
###################
def PID_prog(vm: LiveMode, PDH_angle: float = 0.0):
    with program() as prog:
        # Results variables
        I = declare(fixed)
        Q = declare(fixed)
        single_shot_DC = declare(fixed)
        single_shot_AC = declare(fixed)
        dc_offset_1 = declare(fixed)
        # PID variables
        vm.declare_variables()
        # Streams
        single_shot_st = declare_stream()
        error_st = declare_stream()
        integrator_error_st = declare_stream()
        derivative_error_st = declare_stream()
        offset_st = declare_stream()

        # Ensure that the results variables are assigned to the measurement elements
        assign_variables_to_element("detector_DC", single_shot_DC)
        assign_variables_to_element("detector_AC", I, Q, single_shot_AC)

        with infinite_loop_():
            # with for_(n, 0, n < N_shots, n + 1):
            # Update the PID parameters based on the user input.
            vm.load_parameters()
            # Ensure that the two digital oscillators will start with the same phase
            reset_phase("phase_modulator")
            reset_phase("detector_AC")
            # Phase angle between the sideband and demodulation in units of 2pi
            frame_rotation_2pi(PDH_angle, "phase_modulator")
            # Sync all the elements
            align()
            # Play the PDH sideband
            play("cw", "phase_modulator")
            # Measure and integrate the signal received by the detector --> DC measurement
            measure(
                "readout",
                "detector_DC",
                None,
                integration.full("constant", single_shot_DC, "out1"),
            )
            # Measure and demodulate the signal received by the detector --> AC measurement sqrt(I**2 + Q**2)
            measure(
                "readout",
                "detector_AC",
                None,
                demod.full("constant", I, "out1"),
                demod.full("constant", Q, "out1"),
            )
            assign(single_shot_AC, I)
            # PID correction signal
            correction, error, int_error, der_error = PID_derivation(single_shot_DC, *vm.variables)
            # Update the DC offset
            assign(dc_offset_1, dc_offset_1 + correction)
            # Handle saturation - Make sure that the DAC won't be asked to output more than 0.5V
            with if_(dc_offset_1 > 0.5 - phase_mod_amplitude):
                assign(dc_offset_1, 0.5 - phase_mod_amplitude)
            with if_(dc_offset_1 < -0.5 + phase_mod_amplitude):
                assign(dc_offset_1, -0.5 + phase_mod_amplitude)
            # Apply the correction
            set_dc_offset("filter_cavity_1", "single", dc_offset_1)

            # Save the desired variables
            save(single_shot_DC, single_shot_st)
            save(dc_offset_1, offset_st)
            save(error, error_st)
            save(der_error, derivative_error_st)
            save(int_error, integrator_error_st)

            # Wait between each iteration
            wait(1000)

        with stream_processing():
            single_shot_st.buffer(1000).save("single_shot")
            offset_st.buffer(1000).save("offset")
            error_st.buffer(1000).save("error")
            integrator_error_st.buffer(1000).save("int_err")
            derivative_error_st.buffer(1000).save("der_err")
    return prog


if __name__ == "__main__":
    # Open the Quantum Machine Manager
    qmm = QuantumMachinesManager(qop_ip, cluster_name=cluster_name)
    # Open the Quantum Machine
    qm = qmm.open_qm(config)
    # Define the parameters to be updated in video mode with their initial value and QUA type
    param_dict = {
        "bitshift_scale_factor": (3, int),
        "gain_P": (-1e-4, fixed),  # The proportional gain
        "gain_I": (0.0, fixed),  # The integration gain
        "gain_D": (0.0, fixed),  # The derivative gain
        "alpha": (0.0, fixed),  # The ratio between integration and proportional error
        "target": (0.0, fixed),  # The target value
    }
    # Initialize the video mode
    video_mode = LiveMode(qm, param_dict)
    # Get the QUA program
    qua_prog = PID_prog(video_mode)
    job = video_mode.execute(qua_prog)
    # Get the results from the OPX in live mode
    data_list = ["error", "int_err", "der_err", "single_shot", "offset"]
    results = fetching_tool(job, data_list, mode="live")
    # Live plotting
    fig = plt.figure()
    while results.is_processing():
        error, int_err, der_err, single_shot, offset = results.fetch_all()
        plt.subplot(231)
        plt.cla()
        plt.plot(error, "-")
        plt.title("Error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.ylabel("Amplitude Error [arb. units]")
        plt.subplot(232)
        plt.cla()
        plt.plot(int_err, "-")
        plt.title("integration_error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.subplot(233)
        plt.cla()
        plt.plot(der_err, "-")
        plt.title("derivative_error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.subplot(234)
        plt.cla()
        plt.plot(single_shot)
        plt.title("Single shot measurement")
        plt.subplot(235)
        plt.cla()
        plt.plot(offset)
        plt.title("Applied offset [V]")
        plt.tight_layout()
        plt.pause(0.1)
