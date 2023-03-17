from qualang_tools.external_frameworks.qcodes.opx_driver import OPX
from qm.qua import *
from typing import Dict
from qcodes.utils.validators import Numbers


# noinspection PyAbstractClass
class OPXCustomSequence(OPX):
    """
    QCoDeS driver for the OPX.

    This specific experiment consists of a custom pulse sequence (to be set with the self.pulse_sequence() attribute)
    embedded in an infinite loop with a pause statement at the beginning of each iteration to allow the synchronization
    with the qcodes do"nd" scans.

    The readout element, operation and duration can be parametrized, as well as the acquisition_mode that can be
    'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'.
    A specific mode for which the OPX will perform a measurement when it receives a trigger can be enabled by setting
    wait_for_trigger(True).

    The parameter sweeps performed by the OPX can also be parametrized using the opx_scan() attribute that can be '0d',
    '1d' or '2d'. The corresponding scan axes are accessible via axis1_start(), axis1_stop() and axis1_step().

    :param config: python dict containing the configuration expected by the OPX.
    :param name: The name of the instrument used internally by QCoDeS. Must be unique.
    :param host: IP address of the router to which the OPX is connected.
    :param port: Port of the OPX or main OPX if working with a cluster.
    """

    def __init__(
        self,
        config: Dict,
        name: str = "OPXCustomSequence",
        host=None,
        port=None,
    ):
        super().__init__(config, name, host=host, port=port)
        self.counter = 0
        self.measurement_variables = None
        self.add_parameter(
            "readout_element",
            unit="",
            initial_value="resonator",
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "readout_operation",
            unit="",
            initial_value="readout",
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "readout_pulse_amplitude",
            unit="V",
            vals=Numbers(-0.5, 0.5 - 2**-16),
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "outer_averaging_loop",
            unit="",
            initial_value=True,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "acquisition_mode",
            unit="",
            initial_value="full_integration",
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "slice_size",
            unit="",
            initial_value=1,
            vals=Numbers(1, 1e6),
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "wait_for_trigger",
            unit="",
            initial_value=False,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "pulse_sequence",
            unit="",
            initial_value=None,
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "n_avg",
            unit="",
            initial_value=1,
            vals=Numbers(1, 1e9),
            get_cmd=None,
            set_cmd=None,
        )
        # opx_scan can be '0d', '1d' or '2d'
        self.add_parameter(
            "opx_scan",
            unit="",
            initial_value="0d",
            get_cmd=None,
            set_cmd=None,
        )
        self.add_parameter(
            "simulation",
            unit="",
            initial_value=False,
            get_cmd=None,
            set_cmd=None,
        )

    # Function to update the readout length
    def update_readout_parameters(self):
        """Update the config with the readout length and amplitude set with self.readout_pulse_length() and self.readout_pulse_amplitude()."""
        if self.readout_pulse_length() % 4 != 0:
            raise ValueError(
                "The readout pulse length must be an integer multiple of 4ns."
            )
        self.config["pulses"]["readout_pulse"]["length"] = int(
            self.readout_pulse_length()
        )
        self.config["integration_weights"]["cosine_weights"]["cosine"] = [
            (1.0, self.config["pulses"]["readout_pulse"]["length"])
        ]
        self.config["integration_weights"]["cosine_weights"]["sine"] = [
            (0.0, self.config["pulses"]["readout_pulse"]["length"])
        ]
        self.config["integration_weights"]["sine_weights"]["cosine"] = [
            (0.0, self.config["pulses"]["readout_pulse"]["length"])
        ]
        self.config["integration_weights"]["sine_weights"]["sine"] = [
            (1.0, self.config["pulses"]["readout_pulse"]["length"])
        ]
        self.config["integration_weights"]["minus_sine_weights"]["cosine"] = [
            (0.0, self.config["pulses"]["readout_pulse"]["length"])
        ]
        self.config["integration_weights"]["minus_sine_weights"]["sine"] = [
            (-1.0, self.config["pulses"]["readout_pulse"]["length"])
        ]
        # update readout pulse amplitude
        pulse = self.config["elements"][self.readout_element()]["operations"][
            self.readout_operation()
        ]
        wf = self.config["pulses"][pulse]["waveforms"]["I"]
        self.config["waveforms"][wf]["sample"] = self.readout_pulse_amplitude()
        # Open QM
        self.open_qm()

    # Declare the QUA variables for the measurement based on the self.acquisition_mode() parameter.
    def measurement_declaration(self):
        """Declare the QUA variables for the measurement based on the self.acquisition_mode() parameter."""
        if self.acquisition_mode() == "raw_adc":
            adc_st = declare_stream(adc_trace=True)
            self.measurement_variables = adc_st
        elif self.acquisition_mode() == "sliced_integration":
            num_segments = int(self.readout_pulse_length() // (4 * self.slice_size()))
            ind = declare(int)
            I_arr = declare(fixed, size=num_segments)
            Q_arr = declare(fixed, size=num_segments)
            I_st = declare_stream()
            Q_st = declare_stream()
            self.measurement_variables = [I_arr, Q_arr, I_st, Q_st, ind, num_segments]
        elif self.acquisition_mode() == "sliced_demodulation":
            num_segments = self.readout_pulse_length() // (4 * self.slice_size())
            ind = declare(int)
            I1_arr = declare(fixed, size=num_segments)
            Q1_arr = declare(fixed, size=num_segments)
            I2_arr = declare(fixed, size=num_segments)
            Q2_arr = declare(fixed, size=num_segments)
            I_st = declare_stream()
            Q_st = declare_stream()
            self.measurement_variables = [
                I1_arr,
                I2_arr,
                I_st,
                Q_st,
                ind,
                num_segments,
                Q1_arr,
                Q2_arr,
            ]
        elif (
            self.acquisition_mode() == "full_integration"
            or self.acquisition_mode() == "full_demodulation"
        ):
            I = declare(fixed)
            Q = declare(fixed)
            I_st = declare_stream()
            Q_st = declare_stream()
            self.measurement_variables = [I, Q, I_st, Q_st]
        else:
            raise Exception(
                f"The acquisition mode '{self.acquisition_mode()}' is not implemented. The available modes are 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'."
            )

    # Create the QUA program corresponding to the measurement mode based on the self.acquisition_mode() parameter.
    def measurement(self):
        """Create the QUA program corresponding to the measurement mode based on the self.acquisition_mode() parameter."""
        self.measurement_declaration()
        variables = self.measurement_variables
        if self.acquisition_mode() == "raw_adc":
            measure(
                self.readout_operation(),
                self.readout_element(),
                variables,
            )
        elif self.acquisition_mode() == "sliced_integration":
            measure(
                self.readout_operation(),
                self.readout_element(),
                None,
                integration.sliced("cos", variables[0], self.slice_size(), "out1"),
                integration.sliced("cos", variables[1], self.slice_size(), "out2"),
            )
            with for_(variables[4], 0, variables[4] < variables[5], variables[4] + 1):
                save(variables[0][variables[4]], variables[2])
                save(variables[1][variables[4]], variables[3])
        elif self.acquisition_mode() == "full_integration":
            measure(
                self.readout_operation(),
                self.readout_element(),
                None,
                integration.full("cos", variables[0], "out1"),
                integration.full("cos", variables[1], "out2"),
            )
            save(variables[0], variables[2])
            save(variables[1], variables[3])
        elif self.acquisition_mode() == "sliced_demodulation":
            measure(
                self.readout_operation(),
                self.readout_element(),
                None,
                demod.sliced("cos", variables[0], self.slice_size(), "out1"),
                demod.sliced("sin", variables[6], self.slice_size(), "out1"),
                demod.sliced("minus_sin", variables[1], self.slice_size(), "out2"),
                demod.sliced("cos", variables[7], self.slice_size(), "out2"),
            )
            with for_(variables[4], 0, variables[4] < variables[5], variables[4] + 1):
                assign(
                    variables[0][variables[4]],
                    variables[0][variables[4]] + variables[6][variables[4]],
                )
                assign(
                    variables[1][variables[4]],
                    variables[1][variables[4]] + variables[7][variables[4]],
                )
                save(variables[0][variables[4]], variables[2])
                save(variables[1][variables[4]], variables[3])
        elif self.acquisition_mode() == "full_demodulation":
            measure(
                self.readout_operation(),
                self.readout_element(),
                None,
                dual_demod.full("cos", "out1", "sin", "out2", variables[0]),
                dual_demod.full("minus_sin", "out1", "cos", "out2", variables[1]),
            )
            save(variables[0], variables[2])
            save(variables[1], variables[3])
        else:
            raise Exception(
                f"The acquisition mode '{self.acquisition_mode()}' is not implemented. The available modes are 'raw_adc', 'full_integration', 'full_demodulation', 'sliced_integration' or 'sliced_demodulation'."
            )

    # Create the stream processing based on the measurement mode (self.acquisition_mode()) and OPX scan 0d, 1d or 2d (self.opx_scan())
    # Right now only 'full_integration' is available with 2d opx scans to avoid overflows
    def stream_results(self):
        """Create the stream processing based on the measurement mode (self.acquisition_mode()) and OPX scan 0d, 1d or 2d (self.opx_scan())"""
        variables = self.measurement_variables
        if self.opx_scan() == "0d":
            if (
                self.acquisition_mode() == "full_integration"
                or self.acquisition_mode() == "full_demodulation"
            ):
                variables[2].buffer(self.n_avg()).map(FUNCTIONS.average()).save_all("I")
                variables[3].buffer(self.n_avg()).map(FUNCTIONS.average()).save_all("Q")
            elif self.acquisition_mode() == "raw_adc":
                variables.input1().buffer(self.n_avg()).map(
                    FUNCTIONS.average()
                ).save_all("adc1")
                variables.input2().buffer(self.n_avg()).map(
                    FUNCTIONS.average()
                ).save_all("adc2")
            elif (
                self.acquisition_mode() == "sliced_integration"
                or self.acquisition_mode() == "sliced_demodulation"
            ):
                variables[2].buffer(variables[5]).buffer(self.n_avg()).map(
                    FUNCTIONS.average()
                ).save_all("I")
                variables[3].buffer(variables[5]).buffer(self.n_avg()).map(
                    FUNCTIONS.average()
                ).save_all("Q")
        elif self.opx_scan() == "1d":
            if (
                self.acquisition_mode() == "full_integration"
                or self.acquisition_mode() == "full_demodulation"
            ):
                variables[2].buffer(self.axis1_npoints()).buffer(self.n_avg()).map(
                    FUNCTIONS.average()
                ).save_all("I")
                variables[3].buffer(self.axis1_npoints()).buffer(self.n_avg()).map(
                    FUNCTIONS.average()
                ).save_all("Q")
            elif self.acquisition_mode() == "raw_adc":
                variables.buffer(self.axis1_npoints()).input1().buffer(
                    self.n_avg()
                ).map(FUNCTIONS.average()).save_all("adc1")
                variables.buffer(self.axis1_npoints()).input2().buffer(
                    self.n_avg()
                ).map(FUNCTIONS.average()).save_all("adc2")
            elif (
                self.acquisition_mode() == "sliced_integration"
                or self.acquisition_mode() == "sliced_demodulation"
            ):
                variables[2].buffer(variables[5]).buffer(self.axis2_npoints()).buffer(
                    self.n_avg()
                ).map(FUNCTIONS.average()).save_all("I")
                variables[3].buffer(variables[5]).buffer(self.axis2_npoints()).buffer(
                    self.n_avg()
                ).map(FUNCTIONS.average()).save_all("Q")
        elif self.opx_scan() == "2d":

            if (
                self.acquisition_mode() == "full_integration"
                or self.acquisition_mode() == "full_demodulation"
            ):
                if self.outer_averaging_loop():
                    variables[2].buffer(self.axis1_npoints()).buffer(
                        self.axis2_npoints()
                    ).buffer(self.n_avg()).map(FUNCTIONS.average()).save_all("I")
                    variables[3].buffer(self.axis1_npoints()).buffer(
                        self.axis2_npoints()
                    ).buffer(self.n_avg()).map(FUNCTIONS.average()).save_all("Q")
                else:
                    variables[2].buffer(self.axis1_npoints()).buffer(self.n_avg()).map(
                        FUNCTIONS.average()
                    ).buffer(self.axis2_npoints()).save_all("I")
                    variables[3].buffer(self.axis1_npoints()).buffer(self.n_avg()).map(
                        FUNCTIONS.average()
                    ).buffer(self.axis2_npoints()).save_all("Q")
            else:
                raise Exception(
                    "It is advises to use 'full_integration' or 'full_demodulation' only for performing 2d scans on the OPX to avoid memory overflow."
                )
        else:
            raise Exception("'scan_opx' must be either '0d', '1d' or '2d'.")

    # Empty method that can be replaced by your pulse sequence in the main script
    # This can also be modified so that you can put the sequences here directly...
    def pulse_sequence(self):
        """Custom pulse sequence"""
        return None

    # Return the QUA program based of the measurement type and the pulse sequence
    def get_prog(self):
        # Update the readout duration and the integration weights
        self.update_readout_parameters()

        with program() as prog:
            # Declare the measurement variables (I, Q, I_st...)
            self.measurement_variables = self.measurement_declaration()
            # Infinite loop and pause() to synchronize with qcodes scans when we are not simulating
            with infinite_loop_():
                if not self.simulation():
                    pause()
                # Wait for the AWG trigger if needed
                if self.wait_for_trigger():
                    wait_for_trigger(self.readout_element())
                    align()
                # Play a custom sequence with the OPX
                self.pulse_sequence(self)

            with stream_processing():
                # Transfer the results from the FPGA to the CPU
                self.stream_results()
        return prog
