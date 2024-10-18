from abc import ABC, abstractmethod
from typing import Tuple
from qm.qua import (
    declare,
    fixed,
    demod,
    set_dc_offset,
    align,
    wait,
    measure,
    QuaVariableType,
    play,
    ramp,
    assign,
    elif_,
    if_,
)
from qm.qua.lib import Cast, Math


class InnerLoopAction(ABC):
    @abstractmethod
    def __call__(self, x: QuaVariableType, y: QuaVariableType) -> Tuple[QuaVariableType, QuaVariableType]:
        pass

    def initial_action(self):
        pass

    def final_action(self):
        pass


class BasicInnerLoopAction(InnerLoopAction):
    """Inner loop action for the video mode: set voltages and measure.

    This class is responsible for performing the inner loop action for the video mode.
    It is used to set the voltages and measure the readout pulse.

    Args:
        x_element: The name of the element along the x-axis to set the voltage.
        y_element: The name of the element along the y-axis to set the voltage.
        readout_element: The name of the element to measure.
        readout_pulse: The name of the pulse to measure.
        pre_measurement_delay: The delay before the measurement.
    """

    def __init__(
        self,
        x_element: str,
        y_element: str,
        readout_element: str,
        readout_pulse: str = "readout",
        pre_measurement_delay: float = 1e-6,
    ):
        self.x_elem = x_element
        self.y_elem = y_element
        self.readout_elem = readout_element
        self.readout_pulse = readout_pulse
        self.pre_measurement_delay = pre_measurement_delay

    def set_dc_offsets(self, x: QuaVariableType, y: QuaVariableType):
        set_dc_offset(self.x_elem, "single", x)
        set_dc_offset(self.y_elem, "single", y)

    def __call__(self, x: QuaVariableType, y: QuaVariableType) -> Tuple[QuaVariableType, QuaVariableType]:
        outputs = {"I": declare(fixed), "Q": declare(fixed)}

        self.set_dc_offsets(x, y)
        align()
        pre_measurement_delay_cycles = int(self.pre_measurement_delay * 1e9 // 4)
        if pre_measurement_delay_cycles >= 4:
            wait(pre_measurement_delay_cycles)
        measure(
            self.readout_pulse,
            self.readout_elem,
            None,
            demod.full("cos", outputs["I"]),
            demod.full("sin", outputs["Q"]),
        )

        return outputs["I"], outputs["Q"]

    def initial_action(self):
        set_dc_offset(self.x_elem, "single", 0)
        set_dc_offset(self.y_elem, "single", 0)
        align()


class BasicInnerLoopActionQuam(InnerLoopAction):
    """Inner loop action for the video mode: set voltages and measure.

    This class is responsible for performing the inner loop action for the video mode.
    It is used to set the voltages and measure the readout pulse.

    Args:
        x_element: The QUAM Channel object along the x-axis.
        y_element: The QUAM Channel object along the y-axis.
        readout_pulse: The QUAM Pulse object to measure.
        pre_measurement_delay: The optional delay before the measurement.
    """

    def __init__(self, x_element, y_element, readout_pulse, pre_measurement_delay: float = 0.0, ramp_rate: float = 0.0):
        self.x_elem = x_element
        self.y_elem = y_element
        self.readout_pulse = readout_pulse
        self.pre_measurement_delay = pre_measurement_delay
        self.ramp_rate = ramp_rate

        self._last_x_voltage = None
        self._last_y_voltage = None

    def perform_ramp(self, element, previous_voltage, new_voltage):
        ramp_cycles_ns_V = declare(int, int(1e9 / self.ramp_rate / 4))
        dV = declare(fixed)
        assign(dV, new_voltage - previous_voltage)
        duration = Math.abs(Cast.mul_int_by_fixed(ramp_cycles_ns_V, dV))
        with if_(duration > 4):
            play(ramp(self.ramp_rate / 1e9), element.name, duration=duration, condition=dV > 0)
            play(ramp(-self.ramp_rate / 1e9), element.name, duration=duration, condition=dV < 0)

    def set_dc_offsets(self, x: QuaVariableType, y: QuaVariableType):
        if self.ramp_rate > 0:
            if getattr(self.x_elem, "sticky", None) is None:
                raise RuntimeError("Ramp rate is not supported for non-sticky elements")
            if getattr(self.y_elem, "sticky", None) is None:
                raise RuntimeError("Ramp rate is not supported for non-sticky elements")

            self.perform_ramp(self.x_elem, self._last_x_voltage, x)
            self.perform_ramp(self.y_elem, self._last_y_voltage, y)
        else:
            self.x_elem.set_dc_offset(x)
            self.y_elem.set_dc_offset(y)

        self._last_x_voltage = x
        self._last_y_voltage = y

    def __call__(self, x: QuaVariableType, y: QuaVariableType) -> Tuple[QuaVariableType, QuaVariableType]:
        self.set_dc_offsets(x, y)
        align()

        pre_measurement_delay_cycles = int(self.pre_measurement_delay * 1e9 // 4)
        if pre_measurement_delay_cycles >= 4:
            wait(pre_measurement_delay_cycles)

        I, Q = self.readout_pulse.channel.measure(self.readout_pulse.id)

        return I, Q

    def initial_action(self):
        self._last_x_voltage = declare(fixed, 0.0)
        self._last_y_voltage = declare(fixed, 0.0)
        self.set_dc_offsets(0, 0)
        align()

    def final_action(self):
        self.set_dc_offsets(0, 0)
        align()
