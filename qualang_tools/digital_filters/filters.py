import warnings
from typing import Tuple, List
import numpy as np
import scipy.signal as sig
from warnings import warn
from enum import Enum


class QOP_VERSION(Enum):
    NONE = {
        "feedforward_max": np.inf,
        "feedback_max": np.inf,
        "feedforward_length": lambda feedback_len: np.inf - 0 * feedback_len,
    }
    QOP222 = {
        "feedforward_max": 2 - 2**-16,
        "feedback_max": 1 - 2**-20,
        "feedforward_length": lambda feedback_len: 44 - 7 * feedback_len,
    }
    QOP220 = {
        "feedforward_max": 2 - 2**-16,
        "feedback_max": 1 - 2**-20,
        "feedforward_length": lambda feedback_len: 44 - 7 * feedback_len,
    }

    @classmethod
    def get_latest(cls):
        """Return the latest QOP version."""
        return cls.QOP222

    @classmethod
    def get_options(cls):
        """Return the list of implemented QOP versions"""
        return [cls.NONE.name, cls.QOP220.name, cls.QOP222.name]


def calc_filter_taps(
    fir: List[float] = None,
    exponential: List[Tuple[float, float]] = None,
    highpass: List[float] = None,
    bounce: List[Tuple[float, float]] = None,
    delay: float = None,
    Ts: float = 1,
    qop_version: Enum = QOP_VERSION.get_latest(),
) -> Tuple[List[float], List[float]]:
    """
    Calculate the best FIR and IIR filter taps for a system with any combination of FIR corrections, exponential
    corrections (undershoot or overshoot), high pass compensation, reflections (bounce corrections) and a needed delay on the line.
    The OPX has hardware constraints that may limit the filter implementation and this is why the running QOP version can be specified as an enum of the class QOP_VERSION.
    The possible options are returned by the `QOP_VERSION.get_options()` method and the default value is given by `QOP_VERSION.get_latest()`.

    Args:
        fir: A list of the needed FIR taps. These would be convoluted with whatever other FIR taps
            are required by the other filters.
        exponential: A list of tuples (A, tau), each tuple represents an exponential decay of the shape
            `1 + A * exp(-t/tau)`. `tau` is in ns. Each exponential correction requires 1 IIR tap and 2 FIR taps.
        highpass: A list of taus, each tau represents a highpass decay of the shape `exp(-t/tau)`.
            `tau` is in ns. Each highpass correction requires 1 IIR tap and 2 FIR taps.
        bounce: A list of tuples (a, tau), each tuple represents a reflection of amplitude `a` happening at time `tau`.
            `tau` is in ns. Note, if `tau` is not a multiple of the sampling rate, multiple FIR taps will be created.
            If `tau` is smaller than 5 taps, accuracy might be lost.
        delay: A global delay to apply using the FIR filters.
            `delay` is in ns. Note, if `delay` is not a multiple of the sampling rate, multiple FIR taps will be
            created. If `delay` is smaller than 5 taps, accuracy might be lost.
        Ts: The sampling rate (in ns) of the system and filter taps.
        qop_version: running QOP version used to format the taps according to the corresponding hardware limitations (ex: QOP_VERSION.QOP222).
    Returns:
        A tuple of two lists.
        The first is a list of FIR (feedforward) taps starting at 0 and spaced `Ts` apart.
        The second is a list of IIR (feedback) taps.
    """
    feedforward_taps = np.array([1.0])
    feedback_taps = np.array([])

    if highpass is not None:
        feedforward_taps, feedback_taps = _iir_correction(highpass, "highpass", feedforward_taps, feedback_taps, Ts)

    if exponential is not None:
        feedforward_taps, feedback_taps = _iir_correction(
            exponential, "exponential", feedforward_taps, feedback_taps, Ts
        )

    if fir is not None:
        feedforward_taps = np.convolve(feedforward_taps, fir)

    if bounce is not None or delay is not None:
        feedforward_taps = bounce_and_delay_correction(
            bounce, delay, feedforward_taps, Ts, qop_version=QOP_VERSION.NONE
        )

    return _check_hardware_limitation(qop_version, feedforward_taps, list(feedback_taps))


def exponential_decay(x, a, t):
    """Function representing the exponential decay defined as 1 + a * np.exp(-x / t).

    :param x: numpy array for the time vector in ns
    :param a: float for the exponential amplitude
    :param t: float for the exponential decay time in ns
    :return: numpy array for the exponential decay
    """
    return 1 + a * np.exp(-x / t)


def high_pass_exponential(x, t):
    """Function representing the exponential decay defined as np.exp(-x / t).

    :param x: numpy array for the time vector in ns
    :param t: float for the exponential decay time in ns
    :return: numpy array for the exponential decay
    """
    return np.exp(-x / t)


def single_exponential_correction(A: float, tau: float, Ts: float = 1, qop_version: Enum = QOP_VERSION.get_latest()):
    """
    Calculate the best FIR and IIR filter taps to correct for an exponential decay (undershoot or overshoot) of the shape
    `1 + A * exp(-t/tau)`.
    The OPX has hardware constraints that may limit the filter implementation and this is why the running QOP version can be specified as an enum of the class QOP_VERSION.
    The possible options are returned by the `QOP_VERSION.get_options()` method and the default value is given by `QOP_VERSION.get_latest()`.

    Args:
        A: The exponential decay pre-factor.
        tau: The time constant for the exponential decay, given in ns.
        Ts: The sampling rate (in ns) of the system and filter taps.
        qop_version: running QOP version used to format the taps according to the corresponding hardware limitations (ex: QOP_VERSION.QOP222).
    Returns:
        A tuple of two items.
        The first is a list of 2 FIR (feedforward) taps starting at 0 and spaced `Ts` apart.
        The second is a single IIR (feedback) tap.
    """
    tau *= 1e-9
    Ts *= 1e-9
    k1 = Ts + 2 * tau * (A + 1)
    k2 = Ts - 2 * tau * (A + 1)
    c1 = Ts + 2 * tau
    c2 = Ts - 2 * tau
    feedback_tap = [-k2 / k1]
    feedforward_taps = list(np.array([c1, c2]) / k1)
    return _check_hardware_limitation(qop_version, feedforward_taps, feedback_tap)


def highpass_correction(tau: float, Ts: float = 1, qop_version: Enum = QOP_VERSION.get_latest()):
    """
    Calculate the best FIR and IIR filter taps to correct for a highpass decay (HPF) of the shape `exp(-t/tau)`.
    The OPX has hardware constraints that may limit the filter implementation and this is why the running QOP version can be specified as an enum of the class QOP_VERSION.
    The possible options are returned by the `QOP_VERSION.get_options()` method and the default value is given by `QOP_VERSION.get_latest()`.

    Args:
        tau: The time constant for the exponential decay, given in ns.
        Ts: The sampling rate (in ns) of the system and filter taps.
        qop_version: running QOP version used to format the taps according to the corresponding hardware limitations (ex: QOP_VERSION.QOP222).
    Returns:
        A tuple of two items.
        The first is a list of 2 FIR (feedforward) taps starting at 0 and spaced `Ts` apart.
        The second is a single IIR (feedback) tap.
    """
    Ts *= 1e-9
    flt = sig.butter(1, np.array([1 / tau / Ts]), btype="highpass", analog=True)
    ahp2, bhp2 = sig.bilinear(flt[1], flt[0], 1e9)
    feedforward_taps = list(np.array([ahp2[0], ahp2[1]]))
    feedback_tap = [bhp2[0]]
    return _check_hardware_limitation(qop_version, feedforward_taps, feedback_tap)


def bounce_and_delay_correction(
    bounce_values: list = (),
    delay: float = 0,
    feedforward_taps: list = (1.0,),
    Ts: float = 1,
    qop_version: Enum = QOP_VERSION.get_latest(),
):
    """
    Calculate the FIR filter taps to correct for reflections (bounce corrections) and to add a delay.
    The OPX has hardware constraints that may limit the filter implementation and this is why the running QOP version can be specified as an enum of the class QOP_VERSION.
    The possible options are returned by the `QOP_VERSION.get_options()` method and the default value is given by `QOP_VERSION.get_latest()`.

    Args:
        bounce_values: A list of tuples (a, tau), each tuple represents a reflection of amplitude `a` happening at time
            `tau`. `tau` is in ns. Note, if `tau` is not a multiple of the sampling rate, multiple FIR taps will be
            created. If `tau` is smaller than 5 taps, accuracy might be lost.
        delay: A global delay to apply using the FIR filters.
            `delay` is in ns. Note, if `delay` is not a multiple of the sampling rate, multiple FIR taps will be
            created. If `delay` is smaller than 5 taps, accuracy might be lost.
        feedforward_taps: Existing FIR (feedforward) taps to be convoluted with the resulting taps.
        Ts: The sampling rate (in ns) of the system and filter taps.
        qop_version: running QOP version used to format the taps according to the corresponding hardware limitations (ex: QOP_VERSION.QOP222).
    Returns:
        A list of FIR (feedforward) taps starting at 0 and spaced `Ts` apart.
    """
    if bounce_values is None:
        bounce_values = []
    if delay is None:
        delay = 0

    if feedforward_taps is None:
        feedforward_taps = [1.0]
    n_extra = 10
    n_taps = 101
    long_taps_x = np.linspace((0 - n_extra) * Ts, (n_taps + n_extra) * Ts, n_taps + 1 + 2 * n_extra)[0:-1]
    feedforward_taps_x = np.linspace(0, (len(feedforward_taps) - 1) * Ts, len(feedforward_taps))

    delay_taps = _get_coefficients_for_delay(delay, long_taps_x, Ts)

    feedforward_taps = np.convolve(feedforward_taps, delay_taps)
    feedforward_taps_x = np.linspace(
        min(feedforward_taps_x) + min(long_taps_x),
        max(feedforward_taps_x) + max(long_taps_x),
        len(feedforward_taps),
    )
    for i, (a, tau) in enumerate(bounce_values):
        bounce_taps = -a * _get_coefficients_for_delay(tau, long_taps_x, Ts)
        bounce_taps[n_extra] += 1
        feedforward_taps = np.convolve(feedforward_taps, bounce_taps)
        feedforward_taps_x = np.linspace(
            min(feedforward_taps_x) + min(long_taps_x),
            max(feedforward_taps_x) + max(long_taps_x),
            len(feedforward_taps),
        )

    feedforward_taps = _round_taps_close_to_zero(feedforward_taps)
    index_start = np.nonzero(feedforward_taps_x == 0)[0][0]
    index_end = np.nonzero(feedforward_taps)[0][-1] + 1
    extra_taps = np.abs(np.concatenate((feedforward_taps[:index_start], feedforward_taps[-index_end:])))
    if np.any(extra_taps > 0.02):  # Contribution is more than 2%
        warnings.warn(f"Contribution from missing taps is not negligible. {max(extra_taps)}")  # todo: improve message

    return _check_hardware_limitation(qop_version, feedforward_taps[index_start:index_end], [])[0]


def _iir_correction(values, filter_type, feedforward_taps, feedback_taps, Ts=1.0):
    b = np.zeros((2, len(values)))
    feedback_taps = np.append(np.zeros(len(values)), feedback_taps)

    if filter_type == "highpass":
        for i, tau in enumerate(values):
            b[:, i], [feedback_taps[i]] = highpass_correction(tau, Ts, qop_version=QOP_VERSION.NONE)
    elif filter_type == "exponential":
        for i, (A, tau) in enumerate(values):
            b[:, i], [feedback_taps[i]] = single_exponential_correction(A, tau, Ts, qop_version=QOP_VERSION.NONE)
    else:
        raise Exception("Unknown filter type")

    for i in range(len(values)):
        feedforward_taps = np.convolve(feedforward_taps, b[:, i])

    return feedforward_taps, feedback_taps


def _get_coefficients_for_delay(tau, full_taps_x, Ts=1.0):
    full_taps = np.sinc((full_taps_x - tau) / Ts)
    full_taps = _round_taps_close_to_zero(full_taps)
    return full_taps


def _round_taps_close_to_zero(taps, accuracy=1e-6):
    taps[np.abs(taps) < accuracy] = 0
    return taps


def _check_hardware_limitation(qop_version: Enum, feedforward_taps: List, feedback_taps: List):
    def _warning_on_one_line(message, category, filename, lineno, file=None, line=None):
        return "%s:%s: %s: %s\n" % (filename, lineno, category.__name__, message)

    warnings.formatwarning = _warning_on_one_line
    warnings.simplefilter("always", UserWarning)

    feedback_taps = np.array(feedback_taps)
    feedforward_taps = np.array(feedforward_taps)

    # Check limitation on the number of feedforward taps
    max_feedforward_len = qop_version.value["feedforward_length"](len(feedback_taps))
    if len(feedforward_taps) > max_feedforward_len:
        warn(
            f"The feedforward taps exceed the maximum length of { qop_version.value['feedforward_length'](len(feedback_taps))} and only the first taps were returned."
        )
        if np.any(feedforward_taps[max_feedforward_len:] > 0.02):  # Contribution is more than 2%
            warnings.warn(
                f"Contribution from missing taps is not negligible: {max(feedforward_taps[max_feedforward_len:]):.3f}"
            )
        feedforward_taps = feedforward_taps[:max_feedforward_len]

    # Check limitation on the max value of a feedback tap
    if np.any(np.abs(feedback_taps) > qop_version.value["feedback_max"]):
        feedback_taps[feedback_taps > qop_version.value["feedback_max"]] = qop_version.value["feedback_max"]
        feedback_taps[feedback_taps < -qop_version.value["feedback_max"]] = -qop_version.value["feedback_max"]
        warn(
            f"The feedback taps reached the maximum value of {qop_version.value['feedback_max']} which may result in a non-optimal filter implementation."
        )

    # Check limitation on the max value of a feedforward tap
    max_value = max(np.abs(feedforward_taps))
    if max_value > qop_version.value["feedforward_max"]:
        feedforward_taps = qop_version.value["feedforward_max"] * feedforward_taps / max_value
        warn(
            f"The feedforward taps reached the maximum value of {qop_version.value['feedforward_max']}. \nThe coefficients are scaled down to stay within the valid range which reduces the outputted amplitude of the pulses played through the filtered port by a factor of {max_value/qop_version.value['feedforward_max']:.3f}."
        )

    return list(feedforward_taps), list(feedback_taps)
