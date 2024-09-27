from qm.qua import declare, fixed, demod, set_dc_offset, align, wait, measure


class InnerLoopAction:
    def __init__(
        self,
        x_element: str,
        y_element: str,
        readout_element: str,
        readout_pulse: str = "readout",
        integration_time=None,
        pre_measurement_delay=None,
    ):
        self.x_elem = x_element
        self.y_elem = y_element
        self.readout_elem = readout_element
        self.readout_pulse = readout_pulse
        self.integration_time = integration_time
        self.pre_measurement_delay = pre_measurement_delay

    @property
    def duration(self):
        if self.integration_time is None or self.pre_measurement_delay is None:
            return None
        return self.integration_time + self.pre_measurement_delay

    def __call__(self, idxs, voltages):
        if self.integration_time is None or self.pre_measurement_delay is None:
            raise ValueError("Integration time and pre-measurement delay must be set")

        I = declare(fixed)
        Q = declare(fixed)

        set_dc_offset(self.x_elem, "single", voltages["x"])
        set_dc_offset(self.y_elem, "single", voltages["y"])
        align()
        if self.pre_measurement_delay >= 16:
            pre_measurement_delay_cycles = int(self.pre_measurement_delay // 4)
            wait(pre_measurement_delay_cycles)
        measure(
            self.readout_pulse,
            self.readout_elem,
            None,
            demod.full("cosine", I),
            demod.full("sine", Q),
            # duration=integration_time // 4,
        )

        return I, Q


class InnerLoopActionQuam:
    def __init__(
        self,
        x_element,
        y_element,
        readout_element,
        readout_pulse: str = "readout",
        integration_time=None,
        pre_measurement_delay=None,
    ):
        self.x_elem = x_element
        self.y_elem = y_element
        self.readout_elem = readout_element
        self.readout_pulse = readout_pulse
        self.integration_time = integration_time
        self.pre_measurement_delay = pre_measurement_delay

    @property
    def duration(self):
        if self.integration_time is None or self.pre_measurement_delay is None:
            return None
        return self.integration_time + self.pre_measurement_delay

    def __call__(self, idxs, voltages):
        if self.integration_time is None or self.pre_measurement_delay is None:
            raise ValueError("Integration time and pre-measurement delay must be set")

        self.x_elem.set_dc_offset(voltages["x"])
        self.y_elem.set_dc_offset(voltages["y"])

        align()
        pre_measurement_delay_cycles = int(self.pre_measurement_delay // 4)
        if pre_measurement_delay_cycles >= 4:
            wait(pre_measurement_delay_cycles)

        I, Q = self.readout_elem.measure(self.readout_pulse)

        return I, Q
