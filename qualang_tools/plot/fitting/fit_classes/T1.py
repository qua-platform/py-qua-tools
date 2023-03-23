from .FittingBaseClass import FittingBaseClass

from typing import List, Union
import numpy as np
import itertools
import matplotlib.pyplot as plt


class T1(FittingBaseClass):

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
        Create a fit to T1 experiment of the form

        .. math::
        f(x) = amp * np.exp(-x * (1/T1)) + final_offset

        for unknown parameters :
            T1 - The decay constant [ns]
            amp - The amplitude [a.u.]
            final_offset -  The offset visible for long waiting times [a.u.]

        :param x_data: The dephasing time [ns]
        :param y_data: Data containing the Ramsey signal
        :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(T1=20))
        :param verbose: if True prints the initial guess and fitting results
        :param plot: if True plots the data and the fitting function
        :param save: if not False saves the data into a json file
                     The id of the file is save='id'. The name of the json file is `id.json`
        :return: A dictionary of (fit_func, T1, amp, final_offset)

        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.time_unit = 'ns' if np.max(x_data) > 10 else 's'

        self.final_offset = None
        self.guess_T1 = None

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
        # Finding a guess for the offset
        self.final_offset = np.mean(self.y[np.min((int(len(self.y) * 0.9), len(self.y) - 3)):])

        # Finding a guess for the decay
        self.guess_T1 = (
                1 / (np.abs(np.polyfit(self.x, np.log(np.abs(self.y - self.final_offset)), 1)[0])) / 2
        )


    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():

            if key == 'T1':
                self.guess_T1 = float(guess) / self.x_normal
            elif key == 'amp':
                pass # why don't we load the amplitude as a guess?
            elif key == 'final_offset':
                self.final_offset = float(guess) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, a0, a1, a2):
        return a1 * self.y[0] * np.exp(-x_var / (self.guess_T1 * a0)) + self.final_offset * a2


    def generate_out_dictionary(self):
        # Output the fitting function and its parameters
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "T1": [(self.guess_T1 * self.popt[0]) * self.x_normal, self.perr[0] * self.guess_T1 * self.x_normal],
            "amp": [self.popt[1] * self.y[0] * self.y_normal, self.perr[1] * self.y[0] * self.y_normal],
            "final_offset": [
                self.popt[2] * self.final_offset * self.y_normal,
                self.perr[2] * self.final_offset * self.y_normal,
            ],
        }

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n "
            f"T1 = {self.guess_T1 * self.x_normal:.3f} {self.time_unit}, \n "
            f"amp = {self.y[0] * self.y_normal:.3e} a.u., \n "
            f"final offset = {self.final_offset * self.y_normal:.3e} a.u."
        )

    def print_fit_results(self):
        print(
            f"Fitting results:\n"
            f" T1 = {self.out['T1'][0]:.1f} +/- {self.out['T1'][1]:.1f} {self.time_unit}, \n"
            f" amp = {self.out['amp'][0]:.2e} +/- {self.out['amp'][1]:.1e} a.u., \n"
            f" final offset = {self.out['final_offset'][0]:.2e} +/- {self.out['final_offset'][1]:.1e} a.u."
        )

    def plot_fn(self):
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal, label='fit')
        plt.plot(
            self.x_data,
            self.y_data,
            ".",
            alpha=0.3,
            label=f"T1  = {self.out['T1'][0]:.1f} +/- {self.out['T1'][1]:.1f} {self.time_unit}",
        )
        plt.legend(loc="upper right")

