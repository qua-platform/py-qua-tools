"""Tools to help handling units and conversions.

Content:
    - unit: class containing the relevant units.
    - to_clock_cycles: converts durations from ns to clock cycles.
    - demod2volts: converts demodulated data to volts.
    - raw2volts: converts raw data to volts.
"""

from qm.program._Program import _Program
from inspect import stack
from warnings import warn

class _nanosecond:

    def __init__(self, round_up : bool = False):
        self.round_up = round_up

    def _get_value(self) -> float:

        for frameinfo in stack():
            
            for var in frameinfo.frame.f_locals.values():

                if isinstance(var, _Program): # we have a qua program being declared somewhere
                    if var._is_in_scope: # this is set by __enter__ and unset by __exit__
                        return 0.25 # now it is in clock cycles
        else:
            return 1.0 # this is in nanosecods

    def __mul__(self, other : int | float ) -> int:

        value = self._get_value()

        result, remainder =  divmod(other * value, 1)

        if remainder != 0:

            if self.round_up:
                result +=1

            warn(f'In a qua program we set clock cycles. Value {other} was found NOT to be divisible by 4ns. The timing will be set to {result/value} instead', RuntimeWarning)
            
        return int(result)

    def __rmul__(self, other : int | float ) -> int :
        return self.__mul__(other)

    def __get__(self, obj, type=None):
        return self._get_value()

class unit:


    def __init__(self):
        # Time units
        self._ns = _nanosecond()
        self.cc = 1/4
        
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

    @property
    def ns(self):
        return self._ns._get_value()

    @property
    def us(self):
        return 1e3 * self._ns
    
    @property
    def ms(self):
        return 1e6 * self._ns

    @property
    def s(self):
        return 1e9 * self._ns

    @property
    def clock_cycle(self):
        return 4 * self._ns

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
