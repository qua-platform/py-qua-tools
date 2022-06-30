"""Tools to help handling units and conversions.

Content:
    - unit: class containing the relevant units.
    - to_clock_cycles: converts durations from ns to clock cycles.
    - demod2volts: converts demodulated data to volts.
    - raw2volts: converts raw data to volts.
"""


class unit:
    def __init__(self):
        # Time units
        self.ns = 1
        self.us = 1000
        self.ms = 1000_000
        self.s = 1000_000_000
        self.cc = 1 / 4

        # Frequency units
        self.mHz = 0.001
        self.Hz = 1
        self.kHz = 1000
        self.MHz = 1000_000
        self.GHz = 1000_000_000

        # Voltage units
        self.V = 1
        self.mV = 1e-3
        self.uV = 1e-6

    # conversion functions
    def to_clock_cycles(self, t):
        """Converts a duration to clock cycles.

        :param t: duration in ns.
        :return: duration in clock cycles. It returns only the integer part (floor division).
        """
        if not float(t).is_integer():
            print(
                f"Warning: the specified duration ({t}) to be converted to clock cycles in not an integer. It has been converted to int ({int(t)}) to avoid subsequent errors."
            )
            t = int(t * self.ns)
        return t // 4

    def demod2volts(self, data, duration):
        """Converts the demodulated data to volts.

        :param data: demodulated data. Must be a python variable or array.
        :param duration: demodulation duration in ns.
        :return: the demodulated data in volts.
        """
        return 4096 * data * self.V / duration

    def raw2volts(self, data):
        """Converts the raw data to volts.

        :param data: raw data. Must be a python variable or array.
        :return: the raw data in volts.
        """
        return data * self.V / 4096
