import numpy as np

from qm.qua import declare, assign, play, fixed, Cast, amp, wait, ramp, ramp_to_zero, Math, if_, elif_
from typing import Union, List, Dict, Optional
from warnings import warn
from qm.qua._expressions import QuaExpression, QuaVariable


class VoltageGateSequence:
    def __init__(
        self, configuration: Dict, elements: List[str], time_constants: Optional[Union[int, List[int]]] = None
    ):
        """
        Initializes a VirtualGateSequence object for designing arbitrary pulse sequences using virtual gates.

        This class allows the creation of complex pulse sequences by defining voltage levels (points) in gate-space
        and durations for multiple elements. It supports the addition of steps and ramps, and keeps track of average
        voltage levels for compensation pulses.

        The `configuration` provided will be updated to include necessary operations and waveforms for the sequence.

        **Warning: The framework and compensation pulse derivation is working only for sequences shorter than 8ms.**
        :param configuration: A dictionary representing the OPX configuration (this will be modified)
        :param elements: A list of elements (strings) involved in the virtual gate operations.
        :param time_constants: the value in ns (int) or list of values of the time contants for bias tees on the elements.
        """
        # List of the elements involved in the virtual gates
        self._elements = elements
        # The OPX configuration
        self._config = configuration
        # Determine if bias tee compensation is needed
        self._compensation = False
        if time_constants:
            self._compensation = True
            self._comp_offset = [
                0.0 for _ in self._elements
            ]  # The difference between the voltage applied by the awg before the bias tee and the voltage seen by the device after the bias tee
            # Check if time constants have proper type
            if isinstance(time_constants, int):
                # Accept single int or float, convert to float
                self._time_constants = [time_constants] * len(elements)
                warn(
                    "\nYou have provided a single value for time_constants. All elements are assumed to share this time constant.",
                    stacklevel=2,
                )
            elif isinstance(time_constants, list):
                if len(time_constants) != len(elements):
                    raise ValueError(
                        "If a list is provided for time_constants, its length must match the number of elements."
                    )
                if not all(isinstance(tc, int) for tc in time_constants):
                    raise TypeError("All entries in time_constants must be integers.")
                self._time_constants = time_constants
            else:
                raise TypeError("time_constants must be None, an integer, or a list of integers.")
        # Initialize the current voltage level for sticky elements
        self.current_level = [0.0 for _ in self._elements]
        # Relevant voltage points in the charge stability diagram
        self._voltage_points = {}
        # Keep track of the averaged voltage played for defining the compensation pulse at the end of the sequence
        self.average_power = [0 for _ in self._elements]
        self._expression = None
        self._expression2 = None
        self._voltage_tolerance = 0.001  # limit for adding compensation. must be positive.
        self.base_operation = {}
        # Add to the config the step operation (length=16ns & amp=0.25V)
        for el in self._elements:
            base_amplitude = self._check_amplified_mode(el)
            self.base_operation[el] = {"amplitude": base_amplitude, "bit_shift": int(np.log2(1 / base_amplitude))}
            self._config["elements"][el]["operations"]["step"] = f"{el}_step_pulse"
            self._config["pulses"][f"{el}_step_pulse"] = {
                "operation": "control",
                "length": 16,
                "waveforms": {"single": f"{el}_step_wf"},
            }
            self._config["waveforms"][f"{el}_step_wf"] = {"type": "constant", "sample": base_amplitude}

    def _check_amplified_mode(self, element: str):
        con = self._config["elements"][element]["singleInput"]["port"][0]
        if "type" in self._config["controllers"][con].keys():
            if self._config["controllers"][con]["type"] == "opx1000":
                fem = self._config["elements"][element]["singleInput"]["port"][1]
                ch = self._config["elements"][element]["singleInput"]["port"][2]
                if self._config["controllers"][con]["fems"][fem]["type"] == "LF":
                    if (
                        self._config["controllers"][con]["fems"][fem]["analog_outputs"][ch]["output_mode"]
                        == "amplified"
                    ):
                        return 1.0

        return 0.25

    def _check_name(self, name, key):
        if name in key:
            return self._check_name(name + "%", key)
        else:
            return name

    def _add_op_to_config(self, el: str, name: str, amplitude: float, length: int) -> str:
        """Add an operation to an element when the amplitude is fixed to release the number of real-time operations on
        the OPX.

        :param el: the element to which we want to add the operation.
        :param name: name of the operation.
        :param amplitude: Amplitude of the pulse in V.
        :param length: Duration of the pulse in ns.
        :return : The name of the created operation.
        """
        op_name = self._check_name(name, self._config["elements"][el]["operations"])
        pulse_name = self._check_name(f"{el}_{op_name}_pulse", self._config["pulses"])
        wf_name = self._check_name(f"{el}_{op_name}_wf", self._config["waveforms"])
        self._config["elements"][el]["operations"][op_name] = pulse_name
        self._config["pulses"][pulse_name] = {
            "operation": "control",
            "length": length,
            "waveforms": {"single": wf_name},
        }
        self._config["waveforms"][wf_name] = {"type": "constant", "sample": amplitude}
        return op_name

    @staticmethod
    def _check_duration(duration: int):
        if duration is not None and not __class__.is_QUA(duration):
            if duration == 0:
                warn(
                    "\nThe duration of one level is set to zero, which can cause gaps. Use with care or set it to at least 16ns.",
                    stacklevel=2,
                )
            else:
                assert duration >= 16, "The duration must be at least 16 ns."
                assert duration % 4 == 0, "The duration must be a multiple integer of 4ns."

    def _update_averaged_power(self, level, duration, ramp_duration=None, current_level=None):
        if self.is_QUA(level):
            self._expression = declare(fixed)
            assign(self._expression, level)
            # Multiplication by 1024 to increase the resolution since duration*level must be an integer
            new_average = Cast.mul_int_by_fixed(duration << 10, self._expression)
        elif self.is_QUA(duration):
            new_average = Cast.mul_int_by_fixed(duration << 10, float(level))
        else:
            new_average = int(np.round((level * duration) * 1024))

        if ramp_duration is not None:
            if not self.is_QUA(ramp_duration):
                if self.is_QUA(level):
                    self._expression2 = declare(fixed)
                    assign(self._expression2, (self._expression + current_level) >> 1)
                    new_average += Cast.mul_int_by_fixed(ramp_duration << 10, self._expression2)
                elif self.is_QUA(current_level):
                    expression2 = declare(fixed)
                    assign(expression2, (level + current_level) >> 1)
                    new_average += Cast.mul_int_by_fixed(ramp_duration << 10, expression2)
                elif self.is_QUA(duration):
                    new_average += Cast.mul_int_by_fixed(ramp_duration << 10, (level + current_level) / 2)
                else:
                    new_average += int(np.round(1024 * (level + current_level) * ramp_duration / 2))

            else:
                new_average += Cast.mul_int_by_fixed(ramp_duration << 10, (level + current_level) / 2)
        return new_average

    @staticmethod
    def is_QUA(var):
        return isinstance(var, (QuaExpression, QuaVariable))

    @staticmethod
    def calculate_voltage_offset(voltage, duration, time_constant):
        """Calculates the voltage adjustment of a compensation ramp to account for decay in a bias tee.
        :param voltage (float): Voltage applied at the start of the step
        :param duration (int): Duration of the step in nanoseconds
        :param time_constant (int): Time constant of the bias tee in nanoseconds
        """
        return voltage * duration / time_constant

    def add_step(
        self,
        level: list[Union[float, QuaExpression, QuaVariable]] = None,
        duration: Union[int, QuaExpression, QuaVariable] = None,
        voltage_point_name: str = None,
        ramp_duration: Union[int, QuaExpression, QuaVariable] = None,
    ) -> None:
        """Add a voltage level to the pulse sequence.
        The voltage level is either identified by its voltage_point_name if added to the voltage_point dict beforehand, or by its level and duration.
        A ramp_duration can be used to ramp to the desired level instead of stepping to it.

        :param level: Desired voltage level of the different gates composing the virtual gate in Volt.
        :param duration: How long the voltage level should be maintained in ns. Must be a multiple of 4ns and either larger than 16ns or 0.
        :param voltage_point_name: Name of the voltage level if added to the list of relevant points in the charge stability map.
        :param ramp_duration: Duration in ns of the ramp if the voltage should be ramped to the desired level instead of stepped. Must be a multiple of 4ns and larger than 16ns.
        """
        self._check_duration(duration)
        if isinstance(ramp_duration, (int, float)):
            if ramp_duration == 0:
                ramp_duration = None
        self._check_duration(ramp_duration)
        if ramp_duration is not None:
            if self.is_QUA(ramp_duration):
                warn(
                    "\nYou are using a QUA variable for the ramp duration, make sure to stay at the final voltage level for more than 52ns or errors/gaps may occur, otherwise use a python variable.",
                    stacklevel=2,
                )

        if level is not None:
            if type(level) is not list or len(level) != len(self._elements):
                raise TypeError(
                    "the provided level must be a list of same length as the number of elements involved in the virtual gate."
                )
            level[:] = [float(x) if isinstance(x, int) else x for x in level]

        if voltage_point_name is not None and duration is None:
            _duration = self._voltage_points[voltage_point_name]["duration"]
        elif duration is not None:
            _duration = duration
        else:
            raise RuntimeError(
                "Either the voltage_point_name or the duration and desired voltage level must be provided."
            )

        for i, gate in enumerate(self._elements):
            if voltage_point_name is not None and level is None:
                voltage_level = self._voltage_points[voltage_point_name]["coordinates"][i]
            elif level is not None:
                voltage_point_name = "unregistered_value"
                voltage_level = level[i]
            else:
                raise RuntimeError(
                    "Either the voltage_point_name or the duration and desired voltage level must be provided."
                )
            # Play a step
            if ramp_duration is None:
                self.average_power[i] += self._update_averaged_power(voltage_level, _duration)

                # Dynamic amplitude change...
                if self.is_QUA(voltage_level) or self.is_QUA(self.current_level[i]):
                    # if dynamic duration --> play step and wait
                    if self.is_QUA(_duration):
                        play(
                            "step"
                            * amp((voltage_level - self.current_level[i]) << self.base_operation[gate]["bit_shift"]),
                            gate,
                        )
                        wait((_duration - 16) >> 2, gate)
                    # if constant duration --> new operation and play(*amp(..))
                    else:
                        if _duration > 0:
                            operation = self._add_op_to_config(
                                gate,
                                "step",
                                amplitude=self.base_operation[gate]["amplitude"],
                                length=_duration,
                            )
                            play(
                                operation
                                * amp(
                                    (voltage_level - self.current_level[i]) << self.base_operation[gate]["bit_shift"]
                                ),
                                gate,
                            )

                # Fixed amplitude but dynamic duration --> new operation and play(duration=..)
                elif isinstance(_duration, (QuaExpression, QuaVariable)):
                    operation = self._add_op_to_config(
                        gate,
                        voltage_point_name,
                        amplitude=voltage_level - self.current_level[i],
                        length=16,
                    )
                    play(operation, gate, duration=_duration >> 2)

                # Fixed amplitude and duration --> new operation and play()
                else:
                    operation = self._add_op_to_config(
                        gate,
                        voltage_point_name,
                        amplitude=voltage_level - self.current_level[i],
                        length=_duration,
                    )
                    play(operation, gate)

            # Play a ramp
            else:
                self._check_amplified_mode(gate)  # Check if the amplified mode is used until the bug is fixed
                self.average_power[i] += self._update_averaged_power(
                    voltage_level, _duration, ramp_duration, self.current_level[i]
                )

                if not self.is_QUA(ramp_duration):
                    ramp_rate = 1 / ramp_duration
                    play(ramp((voltage_level - self.current_level[i]) * ramp_rate), gate, duration=ramp_duration >> 2)
                    if self.is_QUA(_duration) or _duration > 0:
                        wait(_duration >> 2, gate)

                else:
                    ramp_rate = declare(fixed)
                    assign(ramp_rate, (voltage_level - self.current_level[i]) * Math.div(1, ramp_duration))
                    play(ramp(ramp_rate), gate, duration=ramp_duration >> 2)
                    if self.is_QUA(_duration):
                        wait((_duration >> 2) - 9, gate)
                    else:
                        if _duration > 0:
                            wait(_duration >> 2, gate)

            self.current_level[i] = voltage_level

    def add_compensation_pulse(self, max_amplitude: float = 0.49, **kwargs) -> None:
        """Add a compensation pulse of the specified amplitude whose duration is derived automatically from the previous operations and the maximum amplitude allowed.
        Note that the derivation of the compensation pulse parameters in real-time may add a gap up to 300ns before playing the pulse, but the voltage will be maintained.
        :param max_amplitude: Maximum amplitude allowed for the compensation pulse in V. Default is 0.49V.
        """
        duration = kwargs.get("duration", None)

        if duration is not None:
            warn(
                "The duration argument is deprecated and will be ignored in future versions. From qualang-tools 0.20, the compensation pulse duration is derived automatically based on the maximum amplitude allowed.",
                DeprecationWarning,
                stacklevel=2,
            )
            self._check_duration(duration)

        for i, gate in enumerate(self._elements):
            if not self.is_QUA(self.average_power[i]):
                if duration is None:
                    # Exact duration of the compensation pulse
                    comp_duration = max(np.abs(0.0009765625 * self.average_power[i] / max_amplitude), 16)
                    # Duration as an integer multiple of 4ns
                    duration_4ns = max((int(np.ceil(comp_duration)) // 4 + 1) * 4, 48)
                    # Corrected amplitude to account for the duration casting to integer
                    amplitude = -np.sign(self.average_power[i]) * max_amplitude * comp_duration / duration_4ns
                    # Apply the compensation pulse as a ramp to circumvent the max amplitude limit.
                    ramp_rate = (amplitude - self.current_level[i]) / 16
                    play(ramp(ramp_rate), gate, duration=4)
                    wait((duration_4ns - 16) // 4, gate)

                else:
                    amplitude = -0.0009765625 * self.average_power[i] / duration
                    operation = self._add_op_to_config(
                        gate, "compensation", amplitude=amplitude - self.current_level[i], length=duration
                    )
                    play(operation, gate)
            else:
                if duration is None:
                    with if_(Math.abs(self.average_power[i]) > (self._voltage_tolerance * 1024)):
                        eval_average_power = declare(int)
                        comp_duration = declare(int)
                        duration_4ns = declare(int)
                        duration_4ns_pow2 = declare(int)
                        duration_4ns_pow2_cur = declare(int)
                        amplitude = declare(fixed)
                        # Exact duration of the compensation pulse
                        # take into account a gap of 110ns for the derivation of the compensation pulse
                        assign(
                            eval_average_power,
                            self.average_power[i] + Cast.mul_int_by_fixed(96 * 1024, self.current_level[i]),
                        )
                        assign(
                            comp_duration,
                            Cast.mul_int_by_fixed(Math.abs(eval_average_power), 0.0009765625 / max_amplitude),
                        )
                        # Ensure that it is larger than 16ns
                        with if_(comp_duration < 16):
                            assign(comp_duration, 16)
                        # Duration as an integer multiple of 4ns
                        assign(duration_4ns, (comp_duration >> 2) << 2)
                        # Take the closest power of 2 for reducing gaps + 1 to avoid sending too much power
                        assign(duration_4ns_pow2, 29 + Math.msb(duration_4ns))
                        # Get the actual compensation pulse duration
                        assign(duration_4ns_pow2_cur, 1 << duration_4ns_pow2)
                        # Corrected amplitude to account for the actual duration with respect to the exact one
                        with if_(eval_average_power > (self._voltage_tolerance * 1024)):
                            assign(amplitude, -Cast.mul_fixed_by_int(max_amplitude >> duration_4ns_pow2, comp_duration))
                        with elif_(eval_average_power < -(self._voltage_tolerance * 1024)):
                            assign(amplitude, Cast.mul_fixed_by_int(max_amplitude >> duration_4ns_pow2, comp_duration))
                        # Apply the compensation pulse as a ramp to circumvent the max amplitude limit.
                        ramp_rate = declare(fixed)
                        assign(ramp_rate, (amplitude - self.current_level[i]) >> 4)
                        play(ramp(ramp_rate), gate, duration=4)
                        wait((duration_4ns_pow2_cur - 16) >> 2, gate)
                else:
                    operation = self._add_op_to_config(
                        gate, "compensation", amplitude=self.base_operation[gate]["amplitude"], length=duration
                    )
                    amplitude = declare(fixed)
                    eval_average_power = declare(int)
                    assign(eval_average_power, self.average_power[i])
                    # 0.0009765625 = 1/1024 to compensate for the 1024 factor in the derivation of self.average_power
                    # The calculation is done in two steps to avoid rounding errors
                    assign(amplitude, -Cast.mul_fixed_by_int(0.01 / duration, eval_average_power))
                    assign(amplitude, amplitude * 0.09765625)
                    play(
                        operation * amp((amplitude - self.current_level[i]) << self.base_operation[gate]["bit_shift"]),
                        gate,
                    )

            self.current_level[i] = amplitude

    def ramp_to_zero(self, duration: int = None):
        """Ramp all the gate voltages down to zero Volt and reset the averaged voltage derived for defining the compensation pulse.

        :param duration: How long will it take for the voltage to ramp down to 0V in clock cycles (4ns). If not
            provided, the default pulse duration defined in the configuration will be used.
        """
        for i, gate in enumerate(self._elements):
            ramp_to_zero(gate, duration)
            self.current_level[i] = 0.0
            self.average_power[i] = 0
        if self._expression is not None:
            assign(self._expression, 0)
        if self._expression2 is not None:
            assign(self._expression2, 0)

    def add_points(self, name: str, coordinates: list, duration: int) -> None:
        """Register a relevant voltage point.

        :param name: Name of the voltage point.
        :param coordinates: Voltage value of each gate involved in the virtual gate in V.
        :param duration: How long should the voltages be maintained at this level in ns. Must be larger than 16ns and a multiple of 4ns.
        """
        self._voltage_points[name] = {}
        self._voltage_points[name]["coordinates"] = [float(x) for x in coordinates]
        self._voltage_points[name]["duration"] = duration
