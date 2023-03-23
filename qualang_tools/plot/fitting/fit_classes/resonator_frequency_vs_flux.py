from .reflection_resonator_spectroscopy import ReflectionResonatorSpectroscopy
from .FittingBaseClass import FittingBaseClass
from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt

class ResonatorFrequencyVsFlux(FittingBaseClass):

    def __init__(
            self,
            frequency: Union[np.ndarray, List[float]],
            flux: Union[np.ndarray, List[float]],
            data: np.ndarray,
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        """
        Create a fit for the resonator frequency versus flux 2D map.
        Each flux points (line-cuts) is fitted with the reflection_resonator_spectroscopy() function to extract the
        resonance frequency of the resonator and the evolution of this frequency versus flux if fitted using

        .. math::
        f(x) = amp * (np.sin((2 * np.pi * f) * frequency + phase))**2 + offset

        for unknown parameters :
            f - The resonator vs flux oscillating frequency [Hz or GHz / V]
            phase - The phase [rad]
            amp - The oscillation amplitude [Hz or GHz]
            offset -  The resonator frequency offset [Hz or GHz]

        :param frequency: The readout frequency [Hz or GHz]
        :param flux: The flux biases [V]
        :param data: Data containing the frequency vs flux map. Must be a 2D array with data.shape=(len(flux), len(frequency)).
        :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(T2=20))
        :param verbose: if True prints the initial guess and fitting results
        :param plot: if True plots the data and the fitting function
        :param save: if not False saves the data into a json file
                     The id of the file is save='id'. The name of the json file is `data_fit_id.json`
          :return: A dictionary of (fit_func, f, phase, amp, offset)

        """

        freq = [np.nan for _ in range(len(flux))]
        # Extract 1D curve f_res vs flux
        self.map2 = np.zeros((len(flux), len(frequency)))
        for i in range(len(flux)):
            try:
                f = ReflectionResonatorSpectroscopy(frequency, data[i])
                freq[i] = f.out["f"][0]
            except (Exception,):
                if i > 0:
                    freq[i] = freq[i - 1]
                else:
                    freq[i] = np.mean(frequency)
            # Get fitted curve on 2D map
            self.map2[i][np.argmin(np.abs(frequency - freq[i]))] = -np.max(data)

        self.freq = freq
        self.frequency = frequency
        self.flux = flux

        super().__init__(flux, freq, guess, verbose, plot, save)

        if np.max(np.abs(frequency)) < 18:
            self.freq_unit = "GHz"
        elif np.max(np.abs(frequency)) < 18000:
            self.freq_unit = "MHz"
        else:
            self.freq_unit = "Hz"

        self.guess_phase = None
        self.offset = None
        self.guess_amp = None
        self.guess_freq = None

        self.generate_initial_params()

        if self.guess is not None:
            self.load_guesses(self.guess)

        if verbose:
            self.print_initial_guesses()

        self.fit_data(p0=[1, 1, self.guess_phase, 1])

        self.generate_out_dictionary()

        if verbose:
            self.print_fit_results()

        if plot:
            self.plot_fn()

        if save:
            self.save()


    def generate_initial_params(self):

        # Compute the FFT for guessing the frequency
        fft = np.fft.fft(self.y)
        f = np.fft.fftfreq(len(self.x))
        # Take the positive part only
        fft = fft[1: len(f) // 2]
        f = f[1: len(f) // 2]
        # Finding a guess for the frequency
        out_freq = f[np.argmax(np.abs(fft))]
        guess_freq = out_freq / (self.x[1] - self.x[0])
        if np.argmax(np.abs(fft)) < 1:
            guess_freq = 1 / (self.x[-1] - self.x[0])

        # Finding a guess for the offset
        self.offset = np.mean(self.y)

        # Finding a guess for the phase
        self.guess_phase = (
                np.angle(fft[np.argmax(np.abs(fft))]) - guess_freq * 2 * np.pi * self.x[0]
        )

        self.guess_amp = np.max(self.y) - np.min(self.y)

    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():
            if key == "f":
                self.guess_freq = float(guess) * self.x_normal
            elif key == "phase":
                self.guess_phase = float(guess)
            elif key == "amp":
                self.guess_amp = float(guess) / self.y_normal
            elif key == "offset":
                self.offset = float(guess) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, a0, a1, a2, a3):
        return (self.guess_amp * a0) * np.sin(
            (2 * np.pi * self.guess_freq * a1) * x_var + a2
        ) + self.offset * a3

    def generate_out_dictionary(self):
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "f": [self.popt[1] * self.guess_freq / self.x_normal, self.perr[1] * self.guess_freq / self.x_normal],
            "phase": [self.popt[2] % (2 * np.pi), self.perr[2] % (2 * np.pi)],
            "amp": [self.popt[0] * self.guess_amp * self.y_normal, self.perr[0] * self.guess_amp * self.y_normal],
            "offset": [
                self.offset * self.popt[3] * self.y_normal,
                self.perr[3] * self.offset * self.y_normal,
            ],
        }

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n"
            f" f = {self.guess_freq / self.x_normal:.3f}, \n"
            f" phase = {self.guess_phase:.3f}, \n"
            f" amplitude = {self.guess_amp * self.y_normal:.3f}, \n"
            f" offset = {self.offset * self.y_normal:.3f}"
        )

    def print_fit_results(self):
        out = self.out
        print(
            f"Fitting results:\n"
            f" f = {out['f'][0]:.3f} +/- {out['f'][1]:.3f} 1/V, \n"
            f" phase = {out['phase'][0]:.3f} +/- {out['phase'][1]:.3f} rad, \n"
            f" amplitude = {out['amp'][0]:.2f} +/- {out['amp'][1]:.3f} {self.freq_unit}, \n"
            f" offset = {out['offset'][0]:.2f} +/- {out['offset'][1]:.3f} {self.freq_unit}"
        )

    def plot_fn(self):
        plt.figure()
        plt.subplot(211)
        plt.pcolor(self.frequency, self.flux, self.map2 + self.data)
        plt.ylabel("Flux bias [V]")
        plt.xlabel(f"Readout frequency [{self.freq_unit}]")
        plt.title("Readout resonator spec vs flux")
        plt.subplot(212)
        plt.plot(self.flux, self.freq, "b.")
        plt.plot(self.flux, self.fit_type(self.x, self.popt) * self.y_normal)
        plt.tight_layout()
        if np.max(np.abs(self.flux)) < 1:
            plt.xlabel("Flux bias [V]")
        else:
            plt.xlabel("Flux bias [mV]")
        plt.ylabel(f"Resonator frequency [{self.freq_unit}]")
        plt.tight_layout()