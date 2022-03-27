import numpy as np

"""
Example of parameters and how the waveforms can be defined:

drag_len = 16  # length of pulse in ns
drag_amp = 0.1  # amplitude of pulse in Volts
drag_del_f = - 0e6  # Detuning frequency in Hz
drag_alpha = 1  # DRAG coefficient
drag_delta = 2 * np.pi * (- 200e6 - drag_del_f)  # in Hz

Gaussian envelope:
drag_gauss_I_wf, drag_gauss_Q_wf = drag_gaussian_pulse_waveforms(drag_amp, drag_len, drag_len / 5, drag_alpha, drag_delta, drag_del_f, subtracted=False)  # pi pulse

Cosine envelope:
drag_cos_I_wf, drag_cos_Q_wf = drag_cosine_pulse_waveforms(drag_amp, drag_len, drag_alpha, drag_delta, drag_del_f)  # pi pulse

"""


def drag_gaussian_pulse_waveforms(
    amplitude, length, sigma, alpha, delta, detuning=0, subtracted=True
):
    """
    Creates a gaussian based DRAG waveforms that compensate for the leakage and for the AC stark shift.

    These DRAG waveforms has been implemented following the next refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :param float sigma: The gaussian standard deviation.
    :param float alpha: The DRAG coefficient.
    :param float detuning: The frequency shift to correct for AC stark shift, in MHz.
    :param float delta: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in MHz.
    :param bool subtracted: If true, returns a subtracted Gaussian, such that the first and last points will be at 0
        volts. This reduces high-frequency components due to the initial and final points offset. Default is true.

    """
    t = np.arange(length, dtype=int)  # An array of size pulse length in ns
    gauss_wave = amplitude * np.exp(
        -((t - length / 2) ** 2) / (2 * sigma ** 2)
    )  # The gaussian function
    gauss_der_wave = (
        amplitude
        * (-2 * 1e9 * (t - length / 2) / (2 * sigma ** 2))
        * np.exp(-((t - length / 2) ** 2) / (2 * sigma ** 2))
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
    Creates a cosine based DRAG waveforms that compensate for the leakage and for the AC stark shift.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    :param float amplitude: The amplitude in volts.
    :param int length: The pulse length in ns.
    :param float sigma: The gaussian standard deviation.
    :param float alpha: The DRAG coefficient.
    :param float detuning: The frequency shift to correct for AC stark shift, in MHz.
    :param float delta: f_21 - f_10 - The differences in energy between the 2-1 and the 1-0 energy levels, in MHz.
    """
    t = np.arange(length, dtype=int)  # An array of size pulse length in ns
    cos_wave = (
        0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / length))
    )  # The cosine function
    sin_wave = (
        0.5 * amplitude * (2 * np.pi / length * 1e9) * np.sin(t * 2 * np.pi / length)
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
