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
from videomode import VideoMode, ParameterTable

target = 0.0  # Set-point to which the PID should converge
angle = 0.0  # Phase angle between the sideband and demodulation in units of 2pi
N_shots = 1000000  # Total number of iterations - can be replaced by an infinite loop

variance_window = 100  # Window to check the convergence of the lock
variance_threshold = 0.0001  # Threshold below which the cavity is considered to be stable
def PID_derivation(input_signal, bitshift_scale_factor, gain_P, gain_I, gain_D, alpha, target):
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

    return gain_P * error + gain_I * integrator_error + gain_D * derivative_error, error, integrator_error, derivative_error


def PID_prog(video_mode: VideoMode):
    with program() as prog:
        n = declare(int)
        test = declare(int, value=[0,1])
        # Results variables
        I = declare(fixed)
        Q = declare(fixed)
        single_shot_DC = declare(fixed)
        single_shot_AC = declare(fixed)
        # PID variables
        video_mode.declare_variables()

        # param_var = declare(int)

        dc_offset_1 = declare(fixed)
        param = declare(int)
        # Variance derivation parameters
        variance_vector = declare(fixed, value=[7 for _ in range(variance_window)])
        variance_index = declare(int, value=0)
        # Streams
        single_shot_st = declare_stream()
        error_st = declare_stream()
        integrator_error_st = declare_stream()
        derivative_error_st = declare_stream()
        offset_st = declare_stream()
        variance_st = declare_stream()

        # Ensure that the results variables are assigned to the measurement elements
        assign_variables_to_element("detector_DC", single_shot_DC)
        assign_variables_to_element("detector_AC", I, Q, single_shot_AC)

        with infinite_loop_():
            # with for_(n, 0, n < N_shots, n + 1):
            # Update the PID parameters based on the user input.
            # IO1 specifies the parameter to be updated and IO2 the corresponding value

            video_mode.load_parameters()
            # Once the parameters are set, this can be used to stop the lock once the cavity is considered stable
            # with while_((Math.abs(Math.max(variance_vector)) - np.abs(target) > variance_threshold) | (Math.abs(Math.min(variance_vector)) - np.abs(target) > variance_threshold)):
            # Ensure that the two digital oscillators will start with the same phase
            reset_phase("phase_modulator")
            reset_phase("detector_AC")
            # Adjust the phase delay between the two
            frame_rotation_2pi(angle, "detector_AC")
            # Sync all the elements
            align()
            # Play the PDH sideband
            play("cw", "phase_modulator")
            # Measure and integrate the signal received by the detector --> DC measurement
            measure("readout", "detector_DC", None, integration.full("constant", single_shot_DC, "out1"))
            # Measure and demodulate the signal received by the detector --> AC measurement sqrt(I**2 + Q**2)
            measure("readout", "detector_AC", None, demod.full("constant", I, "out1"),
                    demod.full("constant", Q, "out1"))
            assign(single_shot_AC, I)
            # PID correction signal
            correction, error, integrator_error, derivative_error = PID_derivation(single_shot_DC, *video_mode.variables)

            # Update the DC offset
            assign(dc_offset_1, dc_offset_1 + correction)
            # Handle saturation - Make sure that channel 6 won't be asked to output more than 0.5V
            with if_(dc_offset_1 > 0.5 - phase_mod_amplitude):
                assign(dc_offset_1, 0.5 - phase_mod_amplitude)
            with if_(dc_offset_1 < -0.5 + phase_mod_amplitude):
                assign(dc_offset_1, -0.5 + phase_mod_amplitude)
            # Apply the correction
            # play("offset" * amp(correction * 4), "filter_cavity_1")
            set_dc_offset("filter_cavity_1", "single", dc_offset_1)

            # Estimate variance (actually simply max distance from target)
            with if_(variance_index == variance_window):
                assign(variance_index, 0)
            assign(variance_vector[variance_index], single_shot_DC)
            save(variance_vector[variance_index], variance_st)
            assign(variance_index, variance_index + 1)

            # Save the desired variables
            save(single_shot_DC, single_shot_st)
            save(dc_offset_1, offset_st)
            save(error, error_st)
            save(derivative_error, derivative_error_st)
            save(integrator_error, integrator_error_st)

            # Wait between each iteration
            wait(1000)

        with stream_processing():
            single_shot_st.buffer(1000).save("single_shot")
            offset_st.buffer(1000).save("offset")
            variance_st.buffer(variance_window).save("variance")
            error_st.buffer(1000).save("error")
            integrator_error_st.buffer(1000).save("integration_error")
            derivative_error_st.buffer(1000).save("derivative_error")
    return prog


if __name__ == "__main__":
    qmm = QuantumMachinesManager(qop_ip, cluster_name="Cluster_83")
    qm = qmm.open_qm(config)
    qm.set_io1_value(0)
    qm.set_io2_value(0.0)

    time.sleep(1)
    # Send the QUA program to the OPX, which compiles and executes it - Execute does not block python!
    param_dict = {"bitshift_scale_factor": 9, "gain_P": -1e-4, "gain_I": 0.0, "gain_D": 0.0, "alpha": 0.0,
                  "target": 0.0}
    video_mode = VideoMode(qm, ParameterTable(param_dict))
    prog = PID_prog(video_mode)
    # from qm import generate_qua_script
    # print(generate_qua_script((prog)))
    video_mode.start(prog)
    job = video_mode.job
    results = fetching_tool(job,
                            ["error", "integration_error", "derivative_error", "single_shot", "offset", "variance"],
                            mode="live")
    fig = plt.figure()
    interrupt_on_close(fig, job)

    while results.is_processing():
        error, integration_error, derivative_error, single_shot, offset, variance = results.fetch_all()

        plt.subplot(231)
        plt.cla()
        plt.plot(error, "-")
        plt.title("Error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.ylabel("Amplitude Error [arb. units]")
        plt.subplot(232)
        plt.cla()
        plt.plot(integration_error, "-")
        plt.title("integration_error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.subplot(233)
        plt.cla()
        plt.plot(derivative_error, "-")
        plt.title("derivative_error signal [a.u.]")
        plt.xlabel("Time [μs]")
        plt.subplot(234)
        plt.cla()
        plt.plot(single_shot)
        plt.title('Single shot measurement')
        plt.subplot(235)
        plt.cla()
        plt.plot(offset)
        plt.title('Applied offset [V]')
        plt.tight_layout()
        plt.pause(0.1)
        # print(np.abs(np.max(variance)) - np.abs(target))
