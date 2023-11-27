import warnings

import numpy as np
import scipy.signal as sig
import matplotlib.pyplot as plt


def calc_filter_taps(fir=None, exponential=None, high_pass=None, bounce=None, delay=None, Ts=1):
    feedforward_taps = np.array([1.0])
    feedback_taps = np.array([])

    if high_pass is not None:
        feedforward_taps, feedback_taps = _iir_correction(high_pass, 'highpass', feedforward_taps, feedback_taps)

    if exponential is not None:
        feedforward_taps, feedback_taps = _iir_correction(exponential, 'exponential', feedforward_taps, feedback_taps)

    if fir is not None:
        feedforward_taps = np.convolve(feedforward_taps, fir)

    if bounce is not None:
        feedforward_taps = np.convolve(feedforward_taps, bounce_correction(bounce))

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


def bounce_correction(values, feedforward_taps, n_taps=11, n_extra=10, Ts=1):
    for i, (a, tau) in enumerate(values):
        full_taps_x = np.linspace(0 - n_extra, n_taps + n_extra, n_taps + 1 + 2 * n_extra)[0:-1]
        full_taps = np.sinc(full_taps_x - tau / Ts)
        extra_taps = np.abs(np.concatenate((full_taps[:n_extra], full_taps[-n_extra:])))
        if np.any(extra_taps > 0.02):  # Contribution is more than 2%
            warnings.warn(f"Contribution from missing taps is not negligible. {max(extra_taps)}")
        bounce_taps = a * full_taps[n_extra:-n_extra]
        bounce_taps[np.abs(bounce_taps) < 1e-6] = 0
        bounce_taps[0] += 1
        bounce_taps = bounce_taps[0:np.nonzero(bounce_taps)[0][-1] + 1]
        feedforward_taps = np.convolve(feedforward_taps, bounce_taps)
    return feedforward_taps
