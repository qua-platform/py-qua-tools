import numpy as np

"""
Example of parameters and how the waveforms can be defined:

drag_len = 16  # length of pulse in ns
drag_amp = 0.1  # amplitude of pulse in Volts
drag_del_f = - 0e6  # Detuning frequency in Hz
drag_alpha = 1  # DRAG coefficient
drag_delta = 2 * np.pi * (- 200e6 - drag_del_f)  # in Hz

Gaussian envelope:
drag_gauss_I_wf, drag_gauss_Q_wf = drag_gaussian_pulse_waveforms(drag_amp, drag_len, drag_len / 5, drag_alpha, drag_delta, drag_del_f, substracted=False)  # pi pulse

Cosine envelope:
drag_cos_I_wf, drag_cos_Q_wf = drag_cosine_pulse_waveforms(drag_amp, drag_len, drag_alpha, drag_delta, drag_del_f)  # pi pulse

"""


def drag_gaussian_pulse_waveforms(
    amplitude, length, sigma, alpha, delta, detune=0, substracted=True
):
    """
    Function that returns DRAG pulses that compensate for leakage and also for the AC stark shift
    that the leakage creates to the qubit frequency.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    Envelope type: gaussian

    :param float amplitude: amplitude in volts
    :param int length: pulse length in ns
    :param float sigma: gaussian standard deviation
    :param float alpha: DRAG coefficient
    :param float detune: frequency shift to correct for AC start shift
    :param float delta: f_21 - f_10 - detune
    :param bool substracted: if you would like to use a substracted gaussian
    """
    t = np.arange(length, dtype=int)  # array of size pulse length in ns
    gauss_wave = amplitude * np.exp(
        -((t - length / 2) ** 2) / (2 * sigma ** 2)
    )  # gaussian function
    gauss_der_wave = (
        amplitude
        * (-2 * 1e9 * (t - length / 2) / (2 * sigma ** 2))
        * np.exp(-((t - length / 2) ** 2) / (2 * sigma ** 2))
    )  # derivative of gaussian
    if substracted:  # if statement to determine usage of subtracted gaussian
        gauss_wave = gauss_wave - gauss_wave[-1]  # subtracted gaussian
    z = gauss_wave + 1j * gauss_der_wave * (alpha / delta)  # complex DRAG envelope
    z *= np.exp(1j * 2 * np.pi * detune * t * 1e-9)  # complex DRAG detuned envelope
    I_wf = z.real.tolist()  # get the real part of the I component of waveform
    Q_wf = z.imag.tolist()  # get the imaginary part for the Q component of waveform
    return I_wf, Q_wf


def drag_cosine_pulse_waveforms(amplitude, length, alpha, delta, detune=0):
    """
    Function that returns DRAG pulses that compensate for leakage and also for the AC stark shift
    that the leakage creates to the qubit frequency.

    These DRAG waveforms has been implemented following the next Refs.:
    Chen et al. PRL, 116, 020501 (2016)
    https://journals.aps.org/prl/abstract/10.1103/PhysRevLett.116.020501
    and Chen's thesis
    https://web.physics.ucsb.edu/~martinisgroup/theses/Chen2018.pdf

    Envelope type: cosine

    :param float amplitude: amplitude of voltage
    :param int length: pulse length
    :param float alpha: DRAG coefficient
    :param float detune: frequency shift to correct for AC start shift
    :param float delta: f_21 - f_10 - detune
    """
    t = np.arange(length, dtype=int)  # array of size pulse length in ns
    cos_wave = 0.5 * amplitude * (1 - np.cos(t * 2 * np.pi / length))  # cosine function
    sin_wave = (
        0.5 * amplitude * (2 * np.pi / length * 1e9) * np.sin(t * 2 * np.pi / length)
    )  # derivative of cos_wave
    z = cos_wave + 1j * sin_wave * (alpha / delta)  # complex DRAG envelope
    z *= np.exp(1j * 2 * np.pi * detune * t * 1e-9)  # complex DRAG detuned envelope
    I_wf = z.real.tolist()  # get the real part for the I component of waveform
    Q_wf = z.imag.tolist()  # get the imaginary part for the Q component of waveform
    return I_wf, Q_wf
