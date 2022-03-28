import numpy as np


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
    )  # The derivative of gaussian
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
    :param float sigma: The gaussian standard deviation.
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
