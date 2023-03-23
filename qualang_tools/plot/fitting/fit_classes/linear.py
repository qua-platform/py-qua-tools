from .FittingBaseClass import FittingBaseClass

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt


class Linear(FittingBaseClass):

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
        Create a linear fit of the form

        .. math::
        f(x) = a * x + b

        for unknown parameters :
             a - The slope of the function
             b - The free parameter of the function

         :param x_data: The data on the x-axis
         :param y_data: The data on the y-axis
         :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(a=20))
         :param verbose: if True prints the initial guess and fitting results
         :param plot: if True plots the data and the fitting function
         :param save: if not False saves the data into a json file
                      The id of the file is save='id'. The name of the json file is `id.json`
         :return: A dictionary of (fit_func, a, b)

        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.a0 = None
        self.b0 = None

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
        # Finding an initial guess to the slope
        self.a0 = (self.y[-1] - self.y[0]) / (self.x[-1] - self.x[0])

        # Finding an initial guess to the free parameter
        self.b0 = self.y[0]


    def load_guesses(self, guess_dict):

        for key, guess in guess_dict.items():

            if key == "a":
                self.a0 = float(guess) * self.x_normal / self.y_normal
            elif key == "b":
                self.b0 = float(guess) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, c0, c1):
        return self.a0 * c0 * x_var + self.b0 * c1

    def generate_out_dictionary(self):
        self.out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "a": [
                self.popt[0] * self.a0 * self.y_normal / self.x_normal,
                self.perr[0] * self.a0 * self.y_normal / self.x_normal,
            ],
            "b": [self.popt[1] * self.b0 * self.y_normal, self.perr[1] * self.b0 * self.y_normal],
        }

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n"
            f" a = {self.a0 * self.y_normal / self.x_normal:.3f}, \n"
            f" b = {self.b0 * self.y_normal:.3f}"
        )

    def print_fit_results(self):
        print(
            f"Fitting results:\n"
            f" a = {self.out['a'][0]:.3f} +/- {self.out['a'][1]:.3f}, \n"
            f" b = {self.out['b'][0]:.3f} +/- {self.out['b'][1]:.3f}"
        )

    def plot_fn(self):
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal)
        plt.plot(
            self.x_data,
            self.y_data,
            ".",
            label=f"a  = {self.out['a'][0]:.1f} +/- {self.out['a'][1]:.1f} \n b  = {self.out['b'][0]:.1f} +/- {self.out['b'][1]:.1f}",
        )
        plt.legend(loc="upper right")