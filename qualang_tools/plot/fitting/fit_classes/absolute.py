from .FittingBaseClass import find_nearest
from .FittingBaseClass import FittingBaseClass

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt


class Absolute(FittingBaseClass):

    def __init__(
            self,
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=None,
            plot=False,
            save=False
    ):
        """
        Fit a function with an absolute linear form :

        f(x) = m * |x - lateral_offset| + vertical_offset

        for unknown parameters:
            gradient - the gradient of the function
            offset - the horizontal offset from zero of the minima of the function
            vertical_offset - the vertical offset from zero of the minima of the function

        @param x: x data
        @param y: y data
        @param guess: dictionary containing initial guesses for the fitting parameters
        @param plot: boolean to dictate whether the fit and data are plotted upon calling the function
        @return:
        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.offset_guess = None
        self.gradient_guess = None
        self.vertical_offset = None

        self.generate_initial_params()

        if self.guess is not None:
            self.load_guesses(self.guess)

        if verbose:
            self.print_initial_guesses()

        self.fit_data(p0=[1, 1, 1])

        self.generate_out_dictionary()

        if verbose:
            self.print_fit_results()

        if plot:
            self.plot_fn()

        if save:
            self.save()

    def generate_initial_params(self):
        self.offset_guess = self.x[find_nearest(self.y, 0)]
        self.gradient_guess = (self.y[-1] - self.y[0]) / (self.x[-1] - self.x[0])
        self.vertical_offset = np.min(self.x)

    def load_guesses(self, guess_dict):
        for key, guess in guess_dict.items():
            if key == 'offset':
                self.offset_guess = float(guess) / self.y_normal
            elif key == 'gradient':
                # unclear if this is right
                self.gradient_guess = float(guess) / self.x_normal * self.y_normal
            elif key == 'vertical_offset':
                self.vertical_offset = float(guess) / self.y_normal
            else:
                raise Exception(
                    f'The key {key} you entered does not match a fitting parameter for this model'
                )

    def func(self, x_var, a0, a1, a2):
        return (a0 * self.gradient_guess) * np.abs(x_var - (a1 * self.offset_guess)) + (self.vertical_offset * a2)

    def generate_out_dictionary(self):
        self.out = {
            'fit_func': lambda x_var: self.fit_type(x_var, self.popt),
            'gradient': self.popt[0] * self.gradient_guess,
            'offset': self.popt[1] * self.offset_guess,
            'vertical_offset': self.popt[2] * self.vertical_offset
        }

    def plot_fn(self):
        # to increase the resolution of fitted line
        use_x = np.linspace(self.x[0], self.x[-1], 1000)
        plt.figure()
        plt.plot(use_x, self.fit_type(use_x, self.popt), label='Fitted data')
        plt.plot(self.x, self.y, '.', label='Raw data')
        plt.legend()

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n "
            f"gradient = {self.gradient_guess * self.x_normal / self.y_normal:.3f} \n "
            f"offset = {self.offset_guess * self.y_normal:.3e} a.u., \n "
            f"vertical_offset = {self.vertical_offset * self.y_normal:.3e} a.u."
        )

    def print_fit_results(self):
        print(
            f"Fitting results:\n"
            f" gradient = {self.out['gradient'][0]:.1f} +/- {self.out['gradient'][1]:.1f} \n"
            f" offset = {self.out['offset'][0]:.2e} +/- {self.out['offset'][1]:.1e} a.u., \n"
            f" vertical offset = {self.out['vertical_offset'][0]:.2e} +/- {self.out['vertical_offset'][1]:.1e} a.u."
        )

