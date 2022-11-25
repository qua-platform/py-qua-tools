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
from typing import Union


class _nanosecond:
    def __init__(self):
        pass

    def _get_value(self) -> float:

        for frameinfo in stack():

            for var in frameinfo.frame.f_locals.values():

                if isinstance(
                    var, _Program
                ):  # we have a qua program being declared somewhere
                    if (
                        var._is_in_scope  # this is set by __enter__ and unset by __exit__ of _Program
                    ):
                        return 0.25  # now it is in clock cycles
        else:
            return 1.0  # this is in nanoseconds

    def __mul__(self, other: Union[int, float]) -> float:

        value = self._get_value()

        return value * other

    def __rmul__(self, other: Union[int, float]) -> float:
        return self.__mul__(other)


class _ensure_integer(float):
    def __new__(cls, value: Union[int, float], verbose: bool = True, *args, **kwargs):
        cls.verbose = verbose
        return super(cls, cls).__new__(cls, value)

    def __mul__(self, other: Union[int, float]) -> int:

        result, remainder = divmod(float(self) * other, 1)

        if remainder != 0:
            if self.verbose:
                warn(
                    f"Warning: the specified duration ({other}) to be converted to clock cycles in not an integer. It has been converted to int ({result}) to avoid subsequent errors.",
                    RuntimeWarning,
                )

        return int(result)

    def __rmul__(self, other: Union[int, float]) -> int:
        return self.__mul__(other)


class unit:
    def __init__(self, coerce_to_integer=False, verbose=True):
        # Time units
        self._ns = _nanosecond()
        self.cc = 1 / 4

        # Handling time units
        self.ensure_integer = coerce_to_integer
        self.verbose = verbose

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
    def ns(self) -> float:
        if self.ensure_integer:
            return _ensure_integer(1 * self._ns, self.verbose)
        else:
            return 1 * self._ns

    @property
    def us(self) -> float:
        if self.ensure_integer:
            return _ensure_integer(1e3 * self._ns, self.verbose)
        else:
            return 1e3 * self._ns

    @property
    def ms(self) -> float:
        if self.ensure_integer:
            return _ensure_integer(1e6 * self._ns, self.verbose)
        else:
            return 1e6 * self._ns

    @property
    def s(self) -> float:
        if self.ensure_integer:
            return _ensure_integer(1e9 * self._ns, self.verbose)
        else:
            return 1e9 * self._ns

    @property
    def clock_cycle(self) -> float:
        if self.ensure_integer:
            return _ensure_integer(4 * self._ns, self.verbose)
        else:
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
