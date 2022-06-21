import numpy as np
from scipy.signal.windows import gaussian


def drag_gaussian_pulse_waveforms(
    amplitude, length, sigma, alpha, delta, detuning=0, subtracted=True
):
    """
    Creates Gaussian based DRAG waveforms that compensate for the leakage and for the AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :param float sigma: The gaussian standard deviation.
    :param float alpha: The DRAG coefficient.
    :param float detuning: The frequency shift to correct for AC stark shift, in Hz.
    :param float delta: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in Hz.
    :param bool subtracted: If true, returns a subtracted Gaussian, such that the first and last points will be at 0
        volts. This reduces high-frequency components due to the initial and final points offset. Default is true.

    """
    t = np.arange(length, dtype=int)  # An array of size pulse length in ns
    center = (length - 1) / 2
    gauss_wave = amplitude * np.exp(
        -((t - center) ** 2) / (2 * sigma ** 2)
    )  # The gaussian function
    gauss_der_wave = (
        amplitude
        * (-2 * 1e9 * (t - center) / (2 * sigma ** 2))
        * np.exp(-((t - center) ** 2) / (2 * sigma ** 2))
    )  # The derivative of the gaussian
    if subtracted:
        gauss_wave = gauss_wave - gauss_wave[-1]  # subtracted gaussian
    z = gauss_wave + 1j * gauss_der_wave * (
        alpha / (delta - detuning)
    )  # The complex DRAG envelope
    z *= np.exp(
        1j * 2 * np.pi * detuning * t * 1e-9
    )  # The complex detuned DRAG envelope
    I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
    Q_wf = z.imag.tolist()  # The `Q` component is the imaginary part of the waveform
    return I_wf, Q_wf


def drag_cosine_pulse_waveforms(amplitude, length, alpha, delta, detuning=0):
    """
    Creates Cosine based DRAG waveforms that compensate for the leakage and for the AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :param float sigma: The Gaussian standard deviation.
    :param float alpha: The DRAG coefficient.
    :param float detuning: The frequency shift to correct for AC stark shift, in Hz.
    :param float delta: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in Hz.
    """
    t = np.arange(length, dtype=int)  # An array of size pulse length in ns
    end_point = length - 1
    cos_wave = (
        0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / end_point))
    )  # The cosine function
    sin_wave = (
        0.5
        * amplitude
        * (2 * np.pi / end_point * 1e9)
        * np.sin(t * 2 * np.pi / end_point)
    )  # The derivative of cosine function
    z = cos_wave + 1j * sin_wave * (
        alpha / (delta - detuning)
    )  # The complex DRAG envelope
    z *= np.exp(
        1j * 2 * np.pi * detuning * t * 1e-9
    )  # The complex detuned DRAG envelope
    I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
    Q_wf = z.imag.tolist()  # The `Q` component is the imaginary part of the waveform
    return I_wf, Q_wf


def flat_top_gaussian(
    amplitude,
    total_length,
    flat_length,
    rise_fall_sigma,
    subtracted=True,
    return_part="all",
):
    """
    Returns a flat top Gaussian. This is a square pulse with a rise and fall of a Gaussian with the given sigma.
    It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.

    :param float amplitude: The amplitude in volts.
    :param int total_length: The total pulse length in ns.
    :param int flat_length: The flat part length in ns.
    :param float rise_fall_sigma: The rise and fall times in ns, taken as a Gaussian standard deviation.
    :param bool subtracted: If true, returns a subtracted Gaussian, such that the first and last points will be at 0
        volts. This reduces high-frequency components due to the initial and final points offset. Default is true.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the  flat part is to scanned from QUA
    """
    gauss_length = total_length - flat_length
    gauss_wave = amplitude * gaussian(gauss_length, rise_fall_sigma)
    if subtracted:
        gauss_wave = gauss_wave - gauss_wave[-1]  # subtracted gaussian
    gauss_wave = gauss_wave.tolist()
    if return_part == "all":
        return (
            gauss_wave[: gauss_length // 2]
            + [amplitude] * flat_length
            + gauss_wave[gauss_length // 2 :]
        )
    elif return_part == "rise":
        return gauss_wave[: gauss_length // 2]
    elif return_part == "fall":
        return gauss_wave[gauss_length // 2 :]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")
