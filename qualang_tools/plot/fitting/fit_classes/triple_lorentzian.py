from .FittingBaseClass import FittingBaseClass

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


class TripleLorentzian(FittingBaseClass):

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
        Create a fit of a - lorentzian for three lorentzians, each with different scaling factors

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

        self.guess_offset = None

        self.guess_x0s = None
        self.guess_lambdas = None
        self.guess_scales = None

        self.generate_initial_params()

        if self.guess is not None:
            self.load_guesses(self.guess)

        if verbose:
            self.print_initial_guesses()

        p0 = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

        self.fit_data(p0)

        self.generate_out_dictionary()

        if verbose:
            self.print_fit_results()

        if plot:
            self.plot_fn()

        if save:
            self.save()

    def generate_initial_params(self):

        # the function is below the offset, so the offset is approximately the maximum value of the function
        self.guess_offset = np.max(self.y)
        height = np.abs(self.guess_offset - np.min(self.y))

        # find x0 guesses (-self.y because it is a maxima finder)
        peaks, peak_properties = signal.find_peaks(-self.y, prominence=0.5 * height)
        self.guess_x0s = self.x[peaks]


        # lambdas are FWHM. Find width of peak at 0.5 prominence --> approx FWHM. peak_widths returns width in samples
        guess_lambdas_samples, _, _, _ = signal.peak_widths(-self.y, peaks=peaks, rel_height=0.5)
        self.guess_lambdas = guess_lambdas_samples * np.abs(self.x[1] - self.x[0])

        # scale guess using definition of lorentzian
        self.guess_scales = (np.pi / 2) * (self.guess_lambdas * height)

    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():
            assert len(guess) == 3, 'please provide guesses as a 3-list (a guess of that parameter for each lorentzian)'
            if key == "lambdas":
                self.guess_lambdas = np.array(guess, dtype=float) / self.x_normal
            elif key == "x0s":
                self.guess_x0s = np.array(guess, dtype=float) / self.x_normal
            elif key == "scales":
                self.guess_scales = np.array(guess, dtype=float) / self.y_normal / self.x_normal
            elif key == "offset":
                self.guess_offset = np.array(guess, dtype=float) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def triple_lorentzian_fn(self, x_var, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9):

        lorentzian_0 = a1 * self.guess_scales[0] / np.pi * (1 / 2 * a2 * self.guess_lambdas[0]) / (
                (x_var - a3 * self.guess_x0s[0]) ** 2 + (1 / 2 * a2 * self.guess_lambdas[0]) ** 2)

        lorentzian_1 = a4 * self.guess_scales[1] / np.pi * (1 / 2 * a5 * self.guess_lambdas[1]) / (
                (x_var - a6 * self.guess_x0s[1]) ** 2 + (1 / 2 * a5 * self.guess_lambdas[1]) ** 2)

        lorentzian_2 = a7 * self.guess_scales[2] / np.pi * (1 / 2 * a8 * self.guess_lambdas[2]) / (
                (x_var - a9 * self.guess_x0s[2]) ** 2 + (1 / 2 * a8 * self.guess_lambdas[2]) ** 2)

        return (a0 * self.guess_offset) - lorentzian_0 - lorentzian_1 - lorentzian_2

    def func(self, *params):
        return self.triple_lorentzian_fn(*params)

    def generate_out_dictionary(self):
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "lambda_0": [self.popt[2] * self.guess_lambdas[0] * self.x_normal,
                         self.perr[2] * self.guess_lambdas[0] * self.x_normal],
            "lambda_1": [self.popt[5] * self.guess_lambdas[1] * self.x_normal,
                         self.perr[5] * self.guess_lambdas[1] * self.x_normal],
            "lambda_2": [self.popt[8] * self.guess_lambdas[2] * self.x_normal,
                         self.perr[8] * self.guess_lambdas[2] * self.x_normal],
            "x0_0": [self.popt[3] * self.guess_x0s[0] * self.x_normal,
                     self.perr[3] * self.guess_x0s[0] * self.x_normal],
            "x0_1": [self.popt[6] * self.guess_x0s[1] * self.x_normal,
                     self.perr[6] * self.guess_x0s[1] * self.x_normal],
            "x0_2": [self.popt[9] * self.guess_x0s[2] * self.x_normal,
                     self.perr[9] * self.guess_x0s[2] * self.x_normal],
            "scale_0": [self.popt[1] * self.guess_scales[0] * self.y_normal * self.x_normal,
                        self.perr[1] * self.guess_scales[0] * self.y_normal * self.x_normal],
            "scale_1": [self.popt[4] * self.guess_scales[1] * self.y_normal * self.x_normal,
                        self.perr[4] * self.guess_scales[1] * self.y_normal * self.x_normal],
            "scale_2": [self.popt[7] * self.guess_scales[2] * self.y_normal * self.x_normal,
                        self.perr[7] * self.guess_scales[2] * self.y_normal * self.x_normal],
            "offset": [
                self.popt[0] * self.guess_offset * self.y_normal,
                self.perr[0] * self.guess_offset * self.y_normal,
            ],
        }

        y_saturated = self.out.get('offset')

        for i in range(3):
            y_peak = self.out.get('fit_func')(self.out.get(f'x0_{i}')[0])

            self.out[f'contrast_{i}'] = [
                (y_saturated[0] - y_peak) / y_saturated[0],
                y_saturated[1] / y_saturated[0]
            ]

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n"
            f" lambda = {self.guess_lambdas * self.x_normal}, \n"
            f" x0 = {self.guess_x0s * self.x_normal}, \n"
            f" scale = {self.guess_scales * self.y_normal * self.x_normal}, \n"
            f" offset = {self.guess_offset * self.y_normal}, \n"
        )

    def print_fit_results(self):
        out = self.out
        print(
            f"Fitting results:\n"
            f" lambda_0 = {out['lambda_0'][0]:.2f} +/- {out['lambda_0'][1]:.3f} a.u., \n"
            f" lambda_1 = {out['lambda_1'][0]:.2f} +/- {out['lambda_1'][1]:.3f} a.u., \n"
            f" lambda_2 = {out['lambda_2'][0]:.2f} +/- {out['lambda_2'][1]:.3f} a.u., \n"
            f" x0_0 = {out['x0_0'][0]:.2f} +/- {out['x0_0'][1]:.3f}, \n"
            f" x0_1 = {out['x0_1'][0]:.2f} +/- {out['x0_1'][1]:.3f}, \n"
            f" x0_2 = {out['x0_2'][0]:.2f} +/- {out['x0_2'][1]:.3f}, \n"
            f" scale_0 = {out['scale_0'][0]:.2f} +/- {out['scale_0'][1]:.3f} a.u., \n"
            f" scale_1 = {out['scale_1'][0]:.2f} +/- {out['scale_1'][1]:.3f} a.u., \n"
            f" scale_2 = {out['scale_2'][0]:.2f} +/- {out['scale_2'][1]:.3f} a.u., \n"
            f" offset = {out['offset'][0]:.2f} +/- {out['offset'][1]:.3f}, \n"
            f" contrast_0 = {out['contrast_0']}\n"
            f" contrast_1 = {out['contrast_1']}\n"
            f" contrast_2 = {out['contrast_2']}\n"

        )

    def plot_fn(self):
        plt.figure()
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal, label='fit')
        plt.scatter(
            self.x_data,
            self.y_data,
            alpha=0.7,
            label='data')
        plt.legend()
        plt.legend(loc="upper right")
        plt.show()
