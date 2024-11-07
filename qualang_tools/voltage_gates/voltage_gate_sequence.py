import numpy as np

from qm.qua._dsl import QuaVariable, QuaExpression
from qm.qua import declare, assign, play, fixed, Cast, amp, wait, ramp, ramp_to_zero
from typing import Union, List, Dict


class VoltageGateSequence:
    def __init__(self, configuration: Dict, elements: List[str]):
        """
        Initializes a VirtualGateSequence object for designing arbitrary pulse sequences using virtual gates.

        This class allows the creation of complex pulse sequences by defining voltage levels (points) in gate-space
        and durations for multiple elements. It supports the addition of steps and ramps, and keeps track of average
        voltage levels for compensation pulses.

        The `configuration` provided will be updated to include necessary operations and waveforms for the sequence.

        :param configuration: A dictionary representing the OPX configuration (this will be modified)
        :param elements: A list of elements (strings) involved in the virtual gate operations.
        """
        # List of the elements involved in the virtual gates
        self._elements = elements
        # The OPX configuration
        self._config = configuration
        # Initialize the current voltage level for sticky elements
        self.current_level = [0.0 for _ in self._elements]
        # Relevant voltage points in the charge stability diagram
        self._voltage_points = {}
        # Keep track of the averaged voltage played for defining the compensation pulse at the end of the sequence
        self.average_power = [0 for _ in self._elements]
        self._expression = None
        self._expression2 = None
        # Add to the config the step operation (length=16ns & amp=0.25V)
        for el in self._elements:
            self._config["elements"][el]["operations"]["step"] = "step_pulse"
        self._config["pulses"]["step_pulse"] = {
            "operation": "control",
            "length": 16,
            "waveforms": {"single": "step_wf"},
        }
        self._config["waveforms"]["step_wf"] = {"type": "constant", "sample": 0.25}

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
        if duration is not None and not isinstance(duration, (QuaVariable, QuaExpression)):
            assert duration >= 4, "The duration must be a larger than 16 ns."

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
                pass
        return new_average

    @staticmethod
    def is_QUA(var):
        return isinstance(var, (QuaVariable, QuaExpression))

    def add_step(
        self,
        level: list[Union[int, QuaExpression, QuaVariable]] = None,
        duration: Union[int, QuaExpression, QuaVariable] = None,
        voltage_point_name: str = None,
        ramp_duration: Union[int, QuaExpression, QuaVariable] = None,
    ) -> None:
        """Add a voltage level to the pulse sequence.
        The voltage level is either identified by its voltage_point_name if added to the voltage_point dict beforehand, or by its level and duration.
        A ramp_duration can be used to ramp to the desired level instead of stepping to it.

        :param level: Desired voltage level of the different gates composing the virtual gate in Volt.
        :param duration: How long the voltage level should be maintained in ns. Must be a multiple of 4ns and larger than 16ns.
        :param voltage_point_name: Name of the voltage level if added to the list of relevant points in the charge stability map.
        :param ramp_duration: Duration in ns of the ramp if the voltage should be ramped to the desired level instead of stepped. Must be a multiple of 4ns and larger than 16ns.
        """
        self._check_duration(duration)
        self._check_duration(ramp_duration)
        if level is not None:
            if type(level) is not list or len(level) != len(self._elements):
                raise TypeError(
                    "the provided level must be a list of same length as the number of elements involved in the virtual gate."
                )

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
                        play("step" * amp((voltage_level - self.current_level[i]) * 4), gate)
                        wait((_duration - 16) >> 2, gate)
                    # if constant duration --> new operation and play(*amp(..))
                    else:
                        operation = self._add_op_to_config(
                            gate,
                            "step",
                            amplitude=0.25,
                            length=_duration,
                        )
                        play(operation * amp((voltage_level - self.current_level[i]) * 4), gate)

                # Fixed amplitude but dynamic duration --> new operation and play(duration=..)
                elif isinstance(_duration, (QuaVariable, QuaExpression)):
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
                self.average_power[i] += self._update_averaged_power(
                    voltage_level, _duration, ramp_duration, self.current_level[i]
                )

                if not self.is_QUA(ramp_duration):
                    ramp_rate = 1 / ramp_duration
                    play(ramp((voltage_level - self.current_level[i]) * ramp_rate), gate, duration=ramp_duration >> 2)
                    wait(_duration >> 2, gate)

            self.current_level[i] = voltage_level

    def add_compensation_pulse(self, duration: int) -> None:
        """Add a compensation pulse of the specified duration whose amplitude is derived from the previous operations.

        :param duration: Duration of the compensation pulse in clock cycles (4ns). Must be larger than 4 clock cycles.
        """
        self._check_duration(duration)
        for i, gate in enumerate(self._elements):
            if not self.is_QUA(self.average_power[i]):
                compensation_amp = -0.001 * self.average_power[i] / duration
                operation = self._add_op_to_config(
                    gate, "compensation", amplitude=compensation_amp - self.current_level[i], length=duration
                )
                play(operation, gate)
            else:
                operation = self._add_op_to_config(gate, "compensation", amplitude=0.25, length=duration)
                compensation_amp = declare(fixed)
                eval_average_power = declare(int)
                assign(eval_average_power, self.average_power[i])
                assign(compensation_amp, -Cast.mul_fixed_by_int(0.0009765625 / duration, eval_average_power))
                play(operation * amp((compensation_amp - self.current_level[i]) * 4), gate)
            self.current_level[i] = compensation_amp

    def ramp_to_zero(self, duration: int = None):
        """Ramp all the gate voltages down to zero Volt and reset the averaged voltage derived for defining the compensation pulse.

        :param duration: How long will it take for the voltage to ramp down to 0V in clock cycles (4ns). If not
            provided, the default pulse duration defined in the configuration will be used.
        """
        for i, gate in enumerate(self._elements):
            ramp_to_zero(gate, duration)
            self.current_level[i] = 0
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
        self._voltage_points[name]["coordinates"] = coordinates
        self._voltage_points[name]["duration"] = duration
