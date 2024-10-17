from qm.qua import declare, fixed, demod, set_dc_offset, align, wait, measure


class InnerLoopAction:
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
        pre_measurement_delay: float = 0.0,
    ):
        self.x_elem = x_element
        self.y_elem = y_element
        self.readout_elem = readout_element
        self.readout_pulse = readout_pulse
        self.pre_measurement_delay = pre_measurement_delay

    def __call__(self, voltages):
        I = declare(fixed)
        Q = declare(fixed)

        set_dc_offset(self.x_elem, "single", voltages["x"])
        set_dc_offset(self.y_elem, "single", voltages["y"])
        align()
        pre_measurement_delay_cycles = int(self.pre_measurement_delay * 1e9 // 4)
        if pre_measurement_delay_cycles >= 4:
            wait(pre_measurement_delay_cycles)
        measure(
            self.readout_pulse,
            self.readout_elem,
            None,
            demod.full("cos", I),
            demod.full("sin", Q),
        )

        return I, Q

    def initial_action(self):
        set_dc_offset(self.x_elem, "single", 0)
        set_dc_offset(self.y_elem, "single", 0)
        align()


class InnerLoopActionQuam:
    """Inner loop action for the video mode: set voltages and measure.

    This class is responsible for performing the inner loop action for the video mode.
    It is used to set the voltages and measure the readout pulse.

    Args:
        x_element: The QUAM Channel object along the x-axis.
        y_element: The QUAM Channel object along the y-axis.
        readout_pulse: The QUAM Pulse object to measure.
        pre_measurement_delay: The optional delay before the measurement.
    """

    def __init__(
        self,
        x_element,
        y_element,
        readout_pulse,
        pre_measurement_delay: float = 0.0,
    ):
        self.x_elem = x_element
        self.y_elem = y_element
        self.readout_pulse = readout_pulse
        self.pre_measurement_delay = pre_measurement_delay

    def __call__(self, voltages):
        self.x_elem.set_dc_offset(voltages["x"])
        self.y_elem.set_dc_offset(voltages["y"])

        align()
        pre_measurement_delay_cycles = int(self.pre_measurement_delay * 1e9 // 4)
        if pre_measurement_delay_cycles >= 4:
            wait(pre_measurement_delay_cycles)

        I, Q = self.readout_pulse.channel.measure(self.readout_pulse.id)

        return I, Q

    def initial_action(self):
        self.x_elem.set_dc_offset(0)
        self.y_elem.set_dc_offset(0)
        align()
