"""Tools to help handling units and conversions.

Content:
    - unit: class containing the relevant units.
    - to_clock_cycles: converts durations from ns to clock cycles.
    - demod2volts: converts demodulated data to volts.
    - raw2volts: converts raw data to volts.
"""

from qm import Program
from inspect import stack
from warnings import warn
from typing import Union
from numpy import round, ndarray, log10, sqrt


class _nanosecond:
    def __init__(self):
        pass

    def _get_value(self) -> float:
        for frameinfo in stack():
            for var in frameinfo.frame.f_locals.values():
                if isinstance(var, Program):  # we have a qua program being declared somewhere
                    if var._is_in_scope:  # this is set by __enter__ and unset by __exit__ of Program
                        return 0.25  # now it is in clock cycles
        else:
            return 1.0  # this is in nanoseconds

    def __mul__(self, other: Union[int, float]) -> float:
        value = self._get_value()

        return value * other

    def __rmul__(self, other: Union[int, float]) -> float:
        return self.__mul__(other)


class _hz:
    def __init__(self):
        pass

    def __mul__(self, other: Union[int, float]) -> float:
        return other

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


class _ensure_rounded_integer(float):
    def __new__(cls, value: Union[int, float], verbose: bool = True, *args, **kwargs):
        cls.verbose = verbose
        return super(cls, cls).__new__(cls, value)

    def __mul__(self, other: Union[int, float]) -> int:
        result, remainder = divmod(float(self) * other, 1)
        if remainder != 0:
            if self.verbose:
                warn(
                    f"Warning: the specified frequency ({other}) to be converted to Hz in not an integer. It has been converted to {int(round(result + remainder))} to avoid subsequent errors.",
                    RuntimeWarning,
                )

        return int(round(result + remainder))

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
        self._Hz = _hz()
        self.mHz = 0.001

        # Voltage units
        self.V = 1
        self.mV = 1e-3
        self.uV = 1e-6

    @property
    def GHz(self) -> float:
        if self.ensure_integer:
            return _ensure_rounded_integer(1e9 * self._Hz, False)
        else:
            return 1e9 * self._Hz

    @property
    def MHz(self) -> float:
        if self.ensure_integer:
            return _ensure_rounded_integer(1e6 * self._Hz, False)
        else:
            return 1e6 * self._Hz

    @property
    def kHz(self) -> float:
        if self.ensure_integer:
            return _ensure_rounded_integer(1e3 * self._Hz, False)
        else:
            return 1e3 * self._Hz

    @property
    def Hz(self) -> float:
        if self.ensure_integer:
            return _ensure_rounded_integer(1 * self._Hz, False)
        else:
            return 1 * self._Hz

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
        return int(t // 4)

    def demod2volts(
        self,
        data: Union[float, ndarray],
        duration: Union[float, int],
        single_demod: bool = False,
    ) -> Union[float, ndarray]:
        """Converts the demodulated data to volts.

        :param data: demodulated data. Must be a python variable or array.
        :param duration: demodulation duration in ns. **WARNING**: this must be the duration of one slice in the case of ```demod.sliced``` and ```demod.accumulated```.
        :param single_demod: Flag to add the additional factor of 2 needed for single demod.
        :return: the demodulated data in volts.
        """
        if single_demod:
            return 2 * 4096 * data * self.V / duration
        else:
            return 4096 * data * self.V / duration

    def volts2demod(
        self,
        value_in_volts: Union[float, ndarray],
        duration: Union[float, int],
        single_demod: bool = False,
    ) -> Union[float, ndarray]:
        """Converts the volts to demodulated data units.

        :param value_in_volts: some value in volts. Must be a python variable or array.
        :param duration: demodulation duration in ns.
        :param single_demod: Flag to add the additional factor of 2 needed for single demod.
        :return: the same value in demodulated data units.
        """
        if single_demod:
            return (value_in_volts * duration) / (2 * 4096 * self.V)
        else:
            return (value_in_volts * duration) / (4096 * self.V)

    def raw2volts(self, data: Union[float, ndarray]) -> Union[float, ndarray]:
        """Converts the raw data to volts.

        :param data: raw data. Must be a python variable or array.
        :return: the raw data in volts.
        """
        return data * self.V / 4096

    @staticmethod
    def volts2dBm(Vp: Union[float, ndarray], Z: Union[float, int] = 50) -> Union[float, ndarray]:
        """Converts the peak voltage (amplitude) from volts to dBm.

        :param Vp: the peak voltage (amplitude) in volts. Must be a python variable or array.
        :param Z: the impedance. Default is 50 ohms.
        :return: the power in dBm.
        """
        return 10 * log10(((Vp / sqrt(2)) ** 2 * 1000) / Z)

    @staticmethod
    def dBm2volts(P_dBm: Union[float, ndarray], Z: Union[float, int] = 50) -> Union[float, ndarray]:
        """Converts the power from dBm to volts (peak voltage or amplitude).

        :param P_dBm: the power in dBm. Must be a python variable or array.
        :param Z: the impedance. Default is 50 ohms.
        :return: the corresponding peak voltage (amplitude) in volts.
        """
        return sqrt(2 * Z / 1000) * 10 ** (P_dBm / 20)
