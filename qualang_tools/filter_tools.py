import warnings
import numpy as np
import scipy.signal as sig


def calc_filter_taps(fir=None, exponential=None, high_pass=None, bounce=None, delay=None, Ts=1):
    feedforward_taps = np.array([1.0])
    feedback_taps = np.array([])

    if high_pass is not None:
        feedforward_taps, feedback_taps = _iir_correction(high_pass, 'highpass', feedforward_taps, feedback_taps)

    if exponential is not None:
        feedforward_taps, feedback_taps = _iir_correction(exponential, 'exponential', feedforward_taps, feedback_taps)

    if fir is not None:
        feedforward_taps = np.convolve(feedforward_taps, fir)

    if bounce is not None or delay is not None:
        if delay is None:
            delay = 0
        if bounce is None:
            bounce = []
        feedforward_taps = bounce_and_delay_correction(bounce, delay, feedforward_taps)

    max_value = max(np.abs(feedforward_taps))

    if max_value >= 2:
        feedforward_taps = 1.5 * feedforward_taps / max_value

    return feedforward_taps, feedback_taps


def _iir_correction(values, filter_type, feedforward_taps, feedback_taps):
    b = np.zeros((2, len(values)))
    feedback_taps = np.append(np.zeros(len(values)), feedback_taps)

    if filter_type == 'highpass':
        for i, tau in enumerate(values):
            b[:, i], feedback_taps[i] = highpass_correction(tau)
    elif filter_type == 'exponential':
        for i, (A, tau) in enumerate(values):
            b[:, i], feedback_taps[i] = exponential_correction(A, tau)
    else:
        raise Exception('Unknown filter type')

    for i in range(len(values)):
        feedforward_taps = np.convolve(feedforward_taps, b[:, i])

    return feedforward_taps, feedback_taps


def exponential_correction(A, tau, Ts=1):
    """
    Insert tau in ns
    """
    tau *= 1e-9
    Ts *= 1e-9
    k1 = Ts + 2 * tau * (A + 1)
    k2 = Ts - 2 * tau * (A + 1)
    c1 = Ts + 2 * tau
    c2 = Ts - 2 * tau
    feedback_tap = k2 / k1
    feedforward_taps = np.array([c1, c2]) / k1
    return feedforward_taps, feedback_tap


def highpass_correction(tau, Ts=1):
    # Find the iir and fir taps based of the time constant
    Ts *= 1e-9
    filts = sig.lti(*sig.butter(1, np.array([1 / tau / Ts]), btype='highpass', analog=True))
    ahp2, bhp2 = sig.bilinear(filts.den, filts.num, 1000e6)
    feedforward_taps = list(np.array([ahp2[0], ahp2[1]]))
    feedback_tap = [min(bhp2[0], 0.9999990463225004)]  # Maximum value for the iir tap
    return feedforward_taps, feedback_tap


def bounce_and_delay_correction(bounce_values, delay, feedforward_taps, Ts=1):
    n_extra = 10
    n_taps = 101
    long_taps_x = np.linspace((0 - n_extra)/Ts, (n_taps + n_extra)/Ts, n_taps + 1 + 2 * n_extra)[0:-1]
    feedforward_taps_x = np.linspace(0, (len(feedforward_taps)-1)/Ts, len(feedforward_taps))

    delay_taps = get_coefficients_for_delay(delay, long_taps_x, Ts)

    feedforward_taps = np.convolve(feedforward_taps, delay_taps)
    feedforward_taps_x = np.linspace(min(feedforward_taps_x) + min(long_taps_x), max(feedforward_taps_x) + max(long_taps_x), len(feedforward_taps))
    for i, (a, tau) in enumerate(bounce_values):
        bounce_taps = a * get_coefficients_for_delay(tau, long_taps_x, Ts)
        bounce_taps[n_extra] += 1
        feedforward_taps = np.convolve(feedforward_taps, bounce_taps)
        feedforward_taps_x = np.linspace(min(feedforward_taps_x) + min(long_taps_x), max(feedforward_taps_x) + max(long_taps_x), len(feedforward_taps))

    feedforward_taps = _round_taps_close_to_zero(feedforward_taps)
    index_start = np.nonzero(feedforward_taps_x == 0)[0][0]
    index_end = np.nonzero(feedforward_taps)[0][-1] + 1
    extra_taps = np.abs(np.concatenate((feedforward_taps[:index_start], feedforward_taps[-index_end:])))
    if np.any(extra_taps > 0.02):  # Contribution is more than 2%
        warnings.warn(f"Contribution from missing taps is not negligible. {max(extra_taps)}")  # todo: improve message
    return feedforward_taps[index_start:index_end]


def get_coefficients_for_delay(tau, full_taps_x, Ts=1):
    full_taps = np.sinc(full_taps_x - tau / Ts)
    full_taps = _round_taps_close_to_zero(full_taps)
    return full_taps


def _round_taps_close_to_zero(taps, accuracy=1e-6):
    taps[np.abs(taps) < accuracy] = 0
    return taps
