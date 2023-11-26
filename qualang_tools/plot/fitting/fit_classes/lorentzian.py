from .FittingBaseClass import FittingBaseClass
from .FittingBaseClass import find_nearest

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt


class Lorentzian(FittingBaseClass):

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
        Create a fit of 1 - lorentzian

        .. math::
        f(x) = offset -  amp * ( (1/pi) * (1/2 gamma) / ((x - x0)**2 + (1/2 gamma)**2))

        for unknown parameters :
            gamma - width parameter
            x0 - centre of the distribution
            offset -  The vertical offset of the distribution
            amp - scaling amplitude

        :param x_data:
        :param y_data:
        :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(T2=20))
        :param verbose: if True prints the initial guess and fitting results
        :param plot: if True plots the data and the fitting function
        :param save: if not False saves the data into a json file
                     The id of the file is save='id'. The name of the json file is `id.json`
          :return: A dictionary of (fit_func, f, phase, tau, amp, uncertainty_population, initial_offset)

        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.guess_x0 = None
        self.guess_offset = None
        self.guess_lambda = None
        self.guess_scale = None


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
        # x0 should be around the minimum of the function
        self.guess_x0 = self.x[np.argmin(self.y)]

        # all of the function is below the offset, so the offset is approximately the maximum value of the function
        self.guess_offset = np.max(self.y)

        # guess FWHM
        height = np.abs(self.guess_offset - np.min(self.y))
        half_maximum = np.min(self.y) + height / 2

        lower_hwhm = self.guess_x0 - self.x[find_nearest(self.y[:np.argmin(self.y)], half_maximum)]
        self.guess_lambda = 2 * lower_hwhm

        # scale guess using definition of lorentzian
        self.guess_scale = (np.pi / 2) * (self.guess_lambda * height)

    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():
            if key == "lambda":
                self.guess_lambda = float(guess) / self.x_normal
            elif key == "x0":
                self.guess_x0 = float(guess) / self.x_normal
            elif key == "scale":
                self.guess_scale = float(guess) / self.y_normal / self.x_normal
            elif key == "offset":
                self.guess_offset = float(guess) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, a0, a1, a2, a3):

        lorentzian = a2 * self.guess_scale / np.pi * (1 / 2 * a0 * self.guess_lambda) / (
                (x_var - a1 * self.guess_x0) ** 2 + (1 / 2 * a0 * self.guess_lambda) ** 2)

        return (a3 * self.guess_offset) - lorentzian

    def generate_out_dictionary(self):
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "lambda": [self.popt[0] * self.guess_lambda * self.x_normal, self.perr[0] * self.guess_lambda * self.x_normal],
            "x0": [self.popt[1] * self.guess_x0 * self.x_normal, self.perr[1] * self.guess_x0 * self.x_normal],
            "scale": [self.popt[2] * self.guess_scale * self.y_normal * self.x_normal, self.perr[2] * self.guess_scale * self.y_normal * self.x_normal],
            "offset": [
                self.popt[3] * self.guess_offset * self.y_normal,
                self.perr[3] * self.guess_offset * self.y_normal,
            ],
        }

        y_peak = self.out.get('fit_func')(self.out.get('x0')[0])
        y_saturated = self.out.get('offset')

        self.out['contrast'] = [
            (y_saturated[0] - y_peak) / y_saturated[0],
            y_saturated[1] / y_saturated[0]
        ]

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n"
            f" lambda = {self.guess_lambda * self.x_normal:.3f}, \n"
            f" x0 = {self.guess_x0 * self.x_normal:.3f}, \n"
            f" scale = {self.guess_scale * self.y_normal * self.x_normal:.3f}, \n"
            f" offset = {self.guess_offset * self.y_normal:.3f}, \n"
        )

    def print_fit_results(self):
        out = self.out
        print(
            f"Fitting results:\n"
            f" lambda = {out['lambda'][0]:.2f} +/- {out['lambda'][1]:.3f} a.u., \n"
            f" x0 = {out['x0'][0]:.2f} +/- {out['x0'][1]:.3f}, \n"
            f" scale = {out['scale'][0]:.2f} +/- {out['scale'][1]:.3f} a.u., \n"
            f" offset = {out['offset'][0]:.2f} +/- {out['offset'][1]:.3f}, \n"
            f" contrast = {out['contrast']}\n"

        )

    def plot_fn(self):
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal, label='fit')
        plt.scatter(
            self.x_data,
            self.y_data,
            alpha=0.7,
            label='data')
        plt.legend()
        plt.legend(loc="upper right")