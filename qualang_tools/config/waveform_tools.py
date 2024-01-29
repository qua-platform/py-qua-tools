import numpy as np
from scipy.signal.windows import gaussian, blackman


def drag_gaussian_pulse_waveforms(
    amplitude, length, sigma, alpha, anharmonicity, detuning=0.0, subtracted=True, sampling_rate=1e9, **kwargs
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
    :param float anharmonicity: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in Hz.
    :param float detuning: The frequency shift to correct for AC stark shift, in Hz.
    :param bool subtracted: If true, returns a subtracted Gaussian, such that the first and last points will be at 0
        volts. This reduces high-frequency components due to the initial and final points offset. Default is true.
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Default is 1G samples/s.
    :return: Returns a tuple of two lists. The first list is the 'I' waveform (real part) and the second is the
        'Q' waveform (imaginary part)
    """
    delta = kwargs.get("delta", None)
    if delta is not None:
        print("'delta' has been replaced by 'anharmonicity' and will be deprecated in the future. ")
        if alpha != 0 and delta == 0:
            raise Exception("Cannot create a DRAG pulse with `anharmonicity=0`")
        t = np.arange(length, step=1e9 / sampling_rate)  # An array of size pulse length in ns
        center = (length - 1e9 / sampling_rate) / 2
        gauss_wave = amplitude * np.exp(-((t - center) ** 2) / (2 * sigma**2))  # The gaussian function
        gauss_der_wave = (
            amplitude * (-2 * 1e9 * (t - center) / (2 * sigma**2)) * np.exp(-((t - center) ** 2) / (2 * sigma**2))
        )  # The derivative of gaussian
        if subtracted:
            gauss_wave = gauss_wave - gauss_wave[-1]  # subtracted gaussian
        z = gauss_wave + 1j * 0
        if alpha != 0:
            # The complex DRAG envelope:
            z += 1j * gauss_der_wave * (alpha / (delta - 2 * np.pi * detuning))
            # The complex detuned DRAG envelope:
            z *= np.exp(1j * 2 * np.pi * detuning * t * 1e-9)
        I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
        Q_wf = z.imag.tolist()  # The `Q` component is the imaginary part of the waveform
    else:
        if alpha != 0 and anharmonicity == 0:
            raise Exception("Cannot create a DRAG pulse with `anharmonicity=0`")
        t = np.arange(length, step=1e9 / sampling_rate)  # An array of size pulse length in ns
        center = (length - 1e9 / sampling_rate) / 2
        gauss_wave = amplitude * np.exp(-((t - center) ** 2) / (2 * sigma**2))  # The gaussian function
        gauss_der_wave = (
            amplitude * (-2 * 1e9 * (t - center) / (2 * sigma**2)) * np.exp(-((t - center) ** 2) / (2 * sigma**2))
        )  # The derivative of gaussian
        if subtracted:
            gauss_wave = gauss_wave - gauss_wave[-1]  # subtracted gaussian
        z = gauss_wave + 1j * 0
        if alpha != 0:
            # The complex DRAG envelope:
            z += 1j * gauss_der_wave * (alpha / (2 * np.pi * anharmonicity - 2 * np.pi * detuning))
            # The complex detuned DRAG envelope:
            z *= np.exp(1j * 2 * np.pi * detuning * t * 1e-9)
        I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
        Q_wf = z.imag.tolist()  # The `Q` component is the imaginary part of the waveform
    return I_wf, Q_wf


def drag_cosine_pulse_waveforms(amplitude, length, alpha, anharmonicity, detuning=0.0, sampling_rate=1e9, **kwargs):
    """
    Creates Cosine based DRAG waveforms that compensate for the leakage and for the AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :param float alpha: The DRAG coefficient.
    :param float anharmonicity: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in Hz.
    :param float detuning: The frequency shift to correct for AC stark shift, in Hz.
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Default is 1G samples/s.
    :return: Returns a tuple of two lists. The first list is the 'I' waveform (real part) and the second is the
        'Q' waveform (imaginary part)
    """
    delta = kwargs.get("delta", None)
    if delta is not None:
        print("'delta' has been replaced by 'anharmonicity' and will be deprecated in the future.")
        if alpha != 0 and anharmonicity == 0:
            raise Exception("Cannot create a DRAG pulse with `anharmonicity=0`")
        t = np.arange(length, step=1e9 / sampling_rate)  # An array of size pulse length in ns
        end_point = length - 1e9 / sampling_rate
        cos_wave = 0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / end_point))  # The cosine function
        sin_wave = (
            0.5 * amplitude * (2 * np.pi / end_point * 1e9) * np.sin(t * 2 * np.pi / end_point)
        )  # The derivative of cosine function
        z = cos_wave + 1j * 0
        if alpha != 0:
            # The complex DRAG envelope:
            z += 1j * sin_wave * (alpha / (delta - 2 * np.pi * detuning))
            # The complex detuned DRAG envelope:
            z *= np.exp(1j * 2 * np.pi * detuning * t * 1e-9)
        I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
        Q_wf = z.imag.tolist()  # The `Q` component is the imaginary part of the waveform
    else:
        if alpha != 0 and anharmonicity == 0:
            raise Exception("Cannot create a DRAG pulse with `anharmonicity=0`")
        t = np.arange(length, step=1e9 / sampling_rate)  # An array of size pulse length in ns
        end_point = length - 1e9 / sampling_rate
        cos_wave = 0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / end_point))  # The cosine function
        sin_wave = (
            0.5 * amplitude * (2 * np.pi / end_point * 1e9) * np.sin(t * 2 * np.pi / end_point)
        )  # The derivative of cosine function
        z = cos_wave + 1j * 0
        if alpha != 0:
            # The complex DRAG envelope:
            z += 1j * sin_wave * (alpha / (2 * np.pi * anharmonicity - 2 * np.pi * detuning))
            # The complex detuned DRAG envelope:
            z *= np.exp(1j * 2 * np.pi * detuning * t * 1e-9)
        I_wf = z.real.tolist()  # The `I` component is the real part of the waveform
        Q_wf = z.imag.tolist()  # The `Q` component is the imaginary part of the waveform
    return I_wf, Q_wf


def flattop_gaussian_waveform(amplitude, flat_length, rise_fall_length, return_part="all", sampling_rate=1e9):
    """
    Returns a flat top Gaussian waveform. This is a square pulse with a rise and fall of a Gaussian with the given
    sigma. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param int rise_fall_length: The rise and fall times in ns. The Gaussian sigma is given by the
        `rise_fall_length / 5`.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the flat part is to scanned from QUA
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Must be an integer multiple of 1e9 samples per seconds. Default is 1G samples/s.
    :return: Returns the waveform as a list of values with 1ns spacing
    """

    assert sampling_rate % 1e9 == 0, "The sampling rate must be an integer multiple of 1e9 samples per second."

    gauss_wave = amplitude * gaussian(
        int(np.round(2 * rise_fall_length * sampling_rate / 1e9)), rise_fall_length / 5 * sampling_rate / 1e9
    )
    rise_part = gauss_wave[: int(rise_fall_length * sampling_rate / 1e9)]
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * int(flat_length * sampling_rate / 1e9) + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")


def flattop_cosine_waveform(amplitude, flat_length, rise_fall_length, return_part="all", sampling_rate=1e9):
    """
    Returns a flat top cosine waveform. This is a square pulse with a rise and fall with cosine shape with the given
    sigma. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param int rise_fall_length: The rise and fall times in ns, taken as the time for a cosine to go from 0 to 1
    (pi phase-shift) and conversely.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the flat part is to scanned from QUA
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Must be an integer multiple of 1e9 samples per seconds. Default is 1G samples/s.
    :return: Returns the waveform as a list of values with 1ns spacing
    """
    assert sampling_rate % 1e9 == 0, "The sampling rate must be an integer multiple of 1e9 samples per second."
    rise_part = amplitude * 0.5 * (1 - np.cos(np.linspace(0, np.pi, int(rise_fall_length * sampling_rate / 1e9))))
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * int(flat_length * sampling_rate / 1e9) + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")


def flattop_tanh_waveform(amplitude, flat_length, rise_fall_length, return_part="all", sampling_rate=1e9):
    """
    Returns a flat top tanh waveform. This is a square pulse with a rise and fall with tanh shape with the given
    sigma. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param int rise_fall_length: The rise and fall times in ns, taken as a number of points of a tanh between -4
        and 4.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the flat part is to scanned from QUA
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Must be an integer multiple of 1e9 samples per seconds. Default is 1G samples/s.
    :return: Returns the waveform as a list of values with 1ns spacing
    """
    assert sampling_rate % 1e9 == 0, "The sampling rate must be an integer multiple of 1e9 samples per second."
    rise_part = amplitude * 0.5 * (1 + np.tanh(np.linspace(-4, 4, int(rise_fall_length * sampling_rate / 1e9))))
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * int(flat_length * sampling_rate / 1e9) + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")


def flattop_blackman_waveform(amplitude, flat_length, rise_fall_length, return_part="all", sampling_rate=1e9):
    """
    Returns a flat top Blackman waveform. This is a square pulse with a rise and fall with Blackman shape with the given
    length. It is possible to only get the rising or falling parts, which allows scanning the flat part length from QUA.
    The length of the pulse will be the `flat_length + 2 * rise_fall_length`.

    :param float amplitude: The amplitude in volts.
    :param int flat_length: The flat part length in ns.
    :param int rise_fall_length: The rise and fall times in ns, taken as the time to go from 0 to 'amplitude'.
    :param str return_part: When set to 'all', returns the complete waveform. Default is 'all'. When set to 'rise',
    returns only the rising part. When set to 'fall', returns only the falling part. This is useful for separating
    the three parts which allows scanning the duration of the  flat part is to scanned from QUA
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Must be an integer multiple of 1e9 samples per seconds. Default is 1G samples/s.
    :return: Returns the waveform as a list
    """
    assert sampling_rate % 1e9 == 0, "The sampling rate must be an integer multiple of 1e9 samples per second."
    backman_wave = amplitude * blackman(2 * int(rise_fall_length * sampling_rate / 1e9))
    rise_part = backman_wave[: int(rise_fall_length * sampling_rate / 1e9)]
    rise_part = rise_part.tolist()
    if return_part == "all":
        return rise_part + [amplitude] * int(flat_length * sampling_rate / 1e9) + rise_part[::-1]
    elif return_part == "rise":
        return rise_part
    elif return_part == "fall":
        return rise_part[::-1]
    else:
        raise Exception("'return_part' must be either 'all', 'rise' or 'fall'")


def blackman_integral_waveform(pulse_length, v_start, v_end, sampling_rate=1e9):
    """
    Returns a Blackman integral waveform. This is the integral of a Blackman waveform, adiabatically going from
    'v_start' to 'v_end' in 'pulse_length' ns.

    :param int pulse_length: The pulse length in ns.
    :param float v_start: The starting amplitude in volts.
    :param float v_end: The ending amplitude in volts.
    :param float sampling_rate: The sampling rate used to describe the waveform, in samples/s. Must be an integer multiple of 1e9 samples per seconds. Default is 1G samples/s.
    :return: Returns the waveform as a list
    """
    assert sampling_rate % 1e9 == 0, "The sampling rate must be an integer multiple of 1e9 samples per second."
    time = np.linspace(0, pulse_length - 1, int(pulse_length * sampling_rate / 1e9))
    black_wave = v_start + (
        time / (pulse_length - 1)
        - (25 / (42 * np.pi)) * np.sin(2 * np.pi * time / (pulse_length - 1))
        + (1 / (21 * np.pi)) * np.sin(4 * np.pi * time / (pulse_length - 1))
    ) * (v_end - v_start)
    return black_wave.tolist()
