from .FittingBaseClass import FittingBaseClass

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt


class Ramsey(FittingBaseClass):

    def __init__(
            self,
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        """
        Create a fit to Ramsey experiment of the form

        .. math::
        f(x) = final_offset * (1 - np.exp(-x * (1/T2))) + amp / 2 * (
            np.exp(-x * (1/T2))
            * (initial_offset * 2 + np.cos(2 * np.pi * f * x + phase))
            )

        for unknown parameters :
            f - The detuning frequency [GHz]
            phase - The phase [rad]
            T2 - The decay constant [ns]
            amp - The amplitude [a.u.]
            final_offset -  The offset visible for long dephasing times [a.u.]
            initial_offset - The offset visible for short dephasing times

        :param x_data: The dephasing time [ns]
        :param y_data: Data containing the Ramsey signal
        :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(T2=20))
        :param verbose: if True prints the initial guess and fitting results
        :param plot: if True plots the data and the fitting function
        :param save: if not False saves the data into a json file
                     The id of the file is save='id'. The name of the json file is `id.json`
          :return: A dictionary of (fit_func, f, phase, tau, amp, uncertainty_population, initial_offset)

        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.guess_freq = None
        self.guess_phase = None
        self.guess_T2 = None
        self.peaks = None
        self.initial_offset = None
        self.final_offset = None

        self.generate_initial_params()

        if self.guess is not None:
            self.load_guesses(self.guess)

        if verbose:
            self.print_initial_guesses()

        self.fit_data(p0=[1, 1, 1, self.guess_phase, 1, 1])

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
        # Remove the DC peak if there is one
        if (np.abs(fft)[1:] - np.abs(fft)[:-1] > 0).any():
            first_read_data_ind = np.where(np.abs(fft)[1:] - np.abs(fft)[:-1] > 0)[0][
                0
            ]  # away from the DC peak
            fft = fft[first_read_data_ind:]
            f = f[first_read_data_ind:]

        # Finding a guess for the frequency
        out_freq = f[np.argmax(np.abs(fft))]
        self.guess_freq = out_freq / (self.x[1] - self.x[0])

        # The period is 1 / guess_freq --> number of oscillations --> peaks decay to get guess_T2
        period = int(np.ceil(1 / out_freq))
        self.peaks = (
                np.array(
                    [
                        np.std(self.y[i * period: (i + 1) * period])
                        for i in range(round(len(self.y) / period))
                    ]
                )
                * np.sqrt(2)
                * 2
        )

        # Finding a guess for the decay (slope of log(peaks))
        if len(self.peaks) > 1:
            self.guess_T2 = (
                    -1
                    / ((np.log(self.peaks)[-1] - np.log(self.peaks)[0]) / (period * (len(self.peaks) - 1)))
                    * (self.x[1] - self.x[0])
            )
        else:
            self.guess_T2 = 100 / self.x_normal

        # Finding a guess for the offsets
        self.initial_offset = np.mean(self.y[:period])
        self.final_offset = np.mean(self.y[-period:])

        # Finding a guess for the phase
        self.guess_phase = (
                np.angle(fft[np.argmax(np.abs(fft))]) - self.guess_freq * 2 * np.pi * self.x[0]
        )

    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():

            if key == "f":
                self.guess_freq = float(guess) * self.x_normal
            elif key == "phase":
                self.guess_phase = float(guess)
            elif key == "T2":
                self.guess_T2 = float(guess) / self.x_normal
            elif key == "amp":
                self.peaks[0] = float(guess) / self.y_normal
            elif key == "initial_offset":
                self.initial_offset = float(guess) / self.y_normal
            elif key == "final_offset":
                self.final_offset = float(guess) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, a0, a1, a2, a3, a4, a5):
        return self.final_offset * a4 * (1 - np.exp(-x_var / (self.guess_T2 * a1))) + self.peaks[
            0
        ] / 2 * a2 * (
                       np.exp(-x_var / (self.guess_T2 * a1))
                       * (
                               a5 * self.initial_offset / self.peaks[0] * 2
                               + np.cos(2 * np.pi * a0 * self.guess_freq * self.x + a3)
                       )
               )

    def generate_out_dictionary(self):
        # Output the fitting function and its parameters
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "f": [self.popt[0] * self.guess_freq / self.x_normal, self.perr[0] * self.guess_freq / self.x_normal],
            "phase": [self.popt[3] % (2 * np.pi), self.perr[3] % (2 * np.pi)],
            "T2": [(self.guess_T2 * self.popt[1]) * self.x_normal, self.perr[1] * self.guess_T2 * self.x_normal],
            "amp": [self.peaks[0] * self.popt[2] * self.y_normal, self.perr[2] * self.peaks[0] * self.y_normal],
            "initial_offset": [
                self.popt[5] * self.initial_offset * self.y_normal,
                self.perr[5] * self.initial_offset * self.y_normal,
            ],
            "final_offset": [
                self.final_offset * self.popt[4] * self.y_normal,
                self.perr[4] * self.final_offset * self.y_normal,
            ],
        }

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n"
            f" f = {self.guess_freq / self.x_normal:.3f}, \n"
            f" phase = {self.guess_phase:.3f}, \n"
            f" T2 = {self.guess_T2 * self.x_normal:.3f}, \n"
            f" amp = {self.peaks[0] * self.y_normal:.3f}, \n"
            f" initial offset = {self.initial_offset * self.y_normal:.3f}, \n"
            f" final_offset = {self.final_offset * self.y_normal:.3f}"
        )

    def print_fit_results(self):

        out = self.out

        print(
            f"Fitting results:\n"
            f" f = {out['f'][0] * 1000:.3f} +/- {out['f'][1] * 1000:.3f} MHz, \n"
            f" phase = {out['phase'][0]:.3f} +/- {out['phase'][1]:.3f} rad, \n"
            f" T2 = {out['T2'][0]:.2f} +/- {out['T2'][1]:.3f} ns, \n"
            f" amp = {out['amp'][0]:.2f} +/- {out['amp'][1]:.3f} a.u., \n"
            f" initial offset = {out['initial_offset'][0]:.2f} +/- {out['initial_offset'][1]:.3f}, \n"
            f" final_offset = {out['final_offset'][0]:.2f} +/- {out['final_offset'][1]:.3f} a.u."
        )

    def plot_fn(self):
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal)
        plt.plot(
            self.x_data,
            self.y_data,
            ".",
            label=f"T2  = {self.out['T2'][0]:.1f} +/- {self.out['T2'][1]:.1f}ns \n f = {self.out['f'][0] * 1000:.3f} +/- {self.out['f'][1] * 1000:.3f} MHz",
        )
        plt.legend(loc="upper right")