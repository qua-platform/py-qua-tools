from .FittingBaseClass import FittingBaseClass
from .FittingBaseClass import find_nearest

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt


class TransmissionResonatorSpectroscopy(FittingBaseClass):

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
        Create a fit to transmission resonator spectroscopy of the form

        .. math::
        ((kc/k) / (
            1 + (4 * ((x - f) ** 2) / (k ** 2)))) + offset

        for unknown parameters:
            f - The frequency at the peak
            kc - The strength with which the field of the resonator couples to the transmission line
            ki - A parameter that indicates the internal coherence properties of the resonator
            k - The FWHM of the fitted function.  k = ki + kc
            offset - The offset

        :param x_data:  The frequency in Hz
        :param y_data: The transition probability (I^2+Q^2)
        :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(f=20e6))
        :param verbose: if True prints the initial guess and fitting results
        :param plot: if True plots the data and the fitting function
        :param save: if not False saves the data into a json file
                     The id of the file is save='id'. The name of the json file is `id.json`
             :return: A dictionary of (fit_func, f, kc, k, ki, offset)

        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.freq_unit = None
        self.f0 = None
        self.offset = None
        self.k = None
        self.peak = None

        self.generate_initial_params()

        if self.guess is not None:
            self.load_guesses(self.guess)

        if verbose:
            self.print_initial_guesses()

        self.fit_data(p0=[1, 1, 1, 1])

        self.generate_out_dictionary()

        if verbose:
            self.print_fit_results()

        if plot:
            self.plot_fn()

        if save:
            self.save()


    def generate_initial_params(self):
        # Finding a guess for the max
        self.peak = max(self.y)
        arg_max = self.y.argmax()

        # Finding an initial guess for the FWHM
        if arg_max > len(self.y) / 2:
            y_FWHM = (self.peak + np.mean(self.y[0:10])) / 2
        else:
            y_FWHM = (self.peak + np.mean(self.y[-10:-1])) / 2

        # Finding a guess for the width
        width0_arg_right = (np.abs(y_FWHM - self.y[arg_max + 1: len(self.y)])).argmin() + arg_max
        width0_arg_left = (np.abs(y_FWHM - self.y[0:arg_max])).argmin()
        width0 = self.x[width0_arg_right] - self.x[width0_arg_left]

        self.k = width0

        # Finding the frequency at the min
        self.f0 = self.x[arg_max]

        # Finding a guess to offset
        self.offset = np.mean(self.y[0: int(width0_arg_left - width0 / 2)])

    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():
            if key == "f":
                self.f0 = float(guess[key]) / self.x_normal
            elif key == "k":
                self.k = float(guess[key]) / self.x_normal
            elif key == "offset":
                self.offset = float(guess[key]) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, a0, a1, a2, a3):
        return (
                       ((self.peak - self.offset) * a0)
                       / (1 + (4 * ((x_var - (self.f0 * a2)) ** 2) / ((self.k * a1) ** 2)))
               ) + (self.offset * a3)

    def generate_out_dictionary(self):
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "f": [self.f0 * self.popt[2] * self.x_normal, self.f0 * self.perr[2] * self.x_normal],
            "kc": [
                (self.peak - self.offset) * self.popt[0] * (self.k * self.popt[1] * self.x_normal) * self.y_normal,
                (self.peak - self.offset) * self.perr[0] * (self.k * self.perr[1] * self.x_normal) * self.y_normal,
            ],
            "ki": [
                (self.popt[1] * self.k * self.x_normal)
                - ((self.peak - self.offset) * self.popt[0] * (self.k * self.popt[1] * self.x_normal) * self.y_normal),
                (self.perr[1] * self.k * self.x_normal)
                - ((self.peak - self.offset) * self.perr[0] * (self.k * self.perr[1] * self.x_normal) * self.y_normal),
            ],
            "k": [self.popt[1] * self.k * self.x_normal, self.perr[1] * self.k * self.x_normal],
            "offset": [self.offset * self.popt[3] * self.y_normal, self.offset * self.perr[3] * self.y_normal],
        }
        # Check freq unit
        if np.max(np.abs(self.x_data)) < 18:
            self.freq_unit = "GHz"
        elif np.max(np.abs(self.x_data)) < 18000:
            self.freq_unit = "MHz"
        else:
            self.freq_unit = "Hz"

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n "
            f" f = {self.f0 * self.x_normal}, \n "
            f" kc = {(self.peak - self.offset) * (self.k * self.x_normal) * self.y_normal}, \n "
            f" k = {self.k * self.x_normal}, \n "
            f" offset = {self.offset * self.y_normal}"
        )

    def print_fit_results(self):
        out = self.out
        print(
            f"Fit results:\n"
            f"f = {out['f'][0]:.3f} +/- {out['f'][1]:.3f} {self.freq_unit}, \n"
            f"kc = {out['kc'][0]:.3f} +/- {out['kc'][1]:.3f} {self.freq_unit}, \n"
            f"ki = {out['ki'][0]:.3f} +/- {out['ki'][1]:.3f} {self.freq_unit}, \n"
            f"k = {out['k'][0]:.3f} +/- {out['k'][1]:.3f} {self.freq_unit}, \n"
            f"offset = {out['offset'][0]:.3f} +/- {out['offset'][1]:.3f} a.u., \n"
        )


    def plot_fn(self):
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal)
        plt.plot(
            self.x_data,
            self.y_data,
            ".",
            label=f"f  = {self.out['f'][0]:.1f} +/- {self.out['f'][1]:.1f} {self.freq_unit}",
        )
        plt.xlabel(f"Frequency {self.freq_unit}")
        plt.legend(loc="upper right")