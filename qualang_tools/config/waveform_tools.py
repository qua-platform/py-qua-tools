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
    :return: Returns a tuple of two lists. The first list is the I waveform (real part) and the second is the
        Q waveform (imaginary part)
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
    :return: Returns a tuple of two lists. The first list is the I waveform (real part) and the second is the
        Q waveform (imaginary part)
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


def flattop_gaussian_waveform(
    amplitude, flat_length, rise_fall_length, return_part="all"
):
    """
    Returns a flat top Gaussian waveform. This is a square pulse with a rise and fall of a Gaussian with the given
    sigma. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param float rise_fall_length: The rise and fall times in ns. The Gaussian sigma is given by the
        `rise_fall_length / 5`.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the flat part is to scanned from QUA
    :return: Returns the waveform as a list of values with 1ns spacing
    """
    gauss_wave = amplitude * gaussian(2 * rise_fall_length, rise_fall_length / 5)

    rise_part = gauss_wave[:rise_fall_length]
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")


def flattop_cosine_waveform(
    amplitude, flat_length, rise_fall_length, return_part="all"
):
    """
    Returns a flat top cosine waveform. This is a square pulse with a rise and fall with cosine shape with the given
    sigma. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param float rise_fall_length: The rise and fall times in ns, taken as the time for a cosine to go from 0 to 1
    (pi phase-shift) and conversely.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the flat part is to scanned from QUA
    :return: Returns the waveform as a list of values with 1ns spacing
    """
    rise_part = 0.5 * (1 - np.cos(np.linspace(0, np.pi, rise_fall_length)))
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")


def flattop_tanh_waveform(amplitude, flat_length, rise_fall_length, return_part="all"):
    """
    Returns a flat top tanh waveform. This is a square pulse with a rise and fall with tanh shape with the given
    sigma. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param float rise_fall_length: The rise and fall times in ns, taken as a number of points of a tanh between -4
        and 4.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the flat part is to scanned from QUA
    :return: Returns the waveform as a list of values with 1ns spacing
    """
    rise_part = 0.5 * (1 + np.tanh(np.linspace(-4, 4, rise_fall_length)))
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")    


def flattop_blackman(amplitude, flat_length, rise_fall_length, return_part="all"):
    """
    Returns a flat top Blackman waveform. This is a square pulse with a rise and fall with Blackman shape with the given
    length. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.
    Amplitude waveform that minimizes the amount of side lobes in the Fourier domain.
    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param float rise_fall_length: The rise and fall times in ns, taken as the time to go from 0 to 'amplitude'.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the  flat part is to scanned from QUA
    :return: Returns the waveform as a list
    """
    time_vector = np.asarray([x * 1.0 for x in range(int(rise_fall_length))])
    rise_part = (
        time_vector / rise_fall_length
        - (25 / (42 * np.pi)) * np.sin(2 * np.pi * time_vector / rise_fall_length)
        + (1 / (21 * np.pi)) * np.sin(4 * np.pi * time_vector / rise_fall_length)
        ) * amplitude
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * flat_length + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")
