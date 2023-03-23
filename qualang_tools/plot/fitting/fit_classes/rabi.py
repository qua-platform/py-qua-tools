from .FittingBaseClass import FittingBaseClass

from typing import List, Union
import numpy as np
import matplotlib.pyplot as plt


class Rabi(FittingBaseClass):

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
        Create a fit to Rabi experiment of the form

        .. math::
        f(x) = amp * (np.sin(0.5 * (2 * np.pi * f) * x_var + phase))**2 * np.exp(-x_var / T) + offset

        for unknown parameters :
            f - The detuning frequency [GHz]
            phase - The phase [rad]
            T - The decay constant [ns]
            amp - The amplitude [a.u.]
            offset -  The offset visible for long dephasing times [a.u.]

        :param x_data: The dephasing time [ns]
        :param y_data: Data containing the Ramsey signal
        :param dict guess: Dictionary containing the initial guess for the fitting parameters (guess=dict(T2=20))
        :param verbose: if True prints the initial guess and fitting results
        :param plot: if True plots the data and the fitting function
        :param save: if not False saves the data into a json file
                     The id of the file is save='id'. The name of the json file is `data_fit_id.json`
          :return: A dictionary of (fit_func, f, phase, tau, amp, uncertainty_population, initial_offset)

        """

        super().__init__(x_data, y_data, guess, verbose, plot, save)

        self.guess_freq = None
        self.guess_phase = None
        self.guess_T = None
        self.guess_amp = None
        self.offset = None

        self.pi_label = None
        self.pi_param = None

        self.generate_initial_params()


        if self.guess is not None:
            self.load_guesses(self.guess)

        if verbose:
            self.print_initial_guesses()



        self.fit_data(p0=[1, 1, 1, self.guess_phase, 1])

        self.generate_out_dictionary()

        # FInd if power rabi or time rabi
        if 0.01 < np.abs(np.max(x_data)) < 1:
            self.pi_param = 0.5 / self.out["f"][0]
            self.pi_label = f"x180 amplitude = {self.pi_param:.3f} V"
        else:
            pi_param = 0.5 / self.out["f"][0]
            if pi_param > 1:
                self.pi_label = f"x180 length = {self.pi_param:.1f} ns"
            else:
                self.pi_label = f"x180 length = {self.pi_param:.3e} s"

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
        self.guess_freq = out_freq / (self.x[1] - self.x[0])
        # If not enough oscillations
        if np.argmax(np.abs(fft)) < 1:
            # If at least 1 oscillation
            if (
                    np.max(np.diff(np.where(self.y < min(self.y) + 0.1 * np.abs(max(self.y) - min(self.y)))))
                    > 1
            ):
                self.guess_freq = 1 / (
                        np.max(
                            np.diff(np.where(self.y < min(self.y) + 0.1 * np.abs(max(self.y) - min(self.y))))
                        )
                        * (self.x[1] - self.x[0])
                )
            # If less than 1 oscillation
            else:
                self.guess_freq = 1 / (
                        (
                                np.argmin(self.y[len(self.y) // 2:])
                                + len(self.y) // 2
                                - np.argmin(self.y[: len(self.y) // 2])
                        )
                        * (self.x[1] - self.x[0])
                )
        # The period is 1 / guess_freq --> number of oscillations --> peaks decay to get guess_T
        period = int(np.ceil(1 / out_freq))
        peaks = (
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
        if len(peaks) > 1:
            self.guess_T = (
                    -1
                    / ((np.log(peaks)[-1] - np.log(peaks)[0]) / (period * (len(peaks) - 1)))
                    * (self.x[1] - self.x[0])
            )
        else:
            self.guess_T = 100 / self.x_normal

        # Finding a guess for the offset
        self.offset = np.mean(self.y[-period:])

        # Finding a guess for the offset
        self.guess_amp = np.abs(np.max(self.y) - np.min(self.y))

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
            elif key == "T":
                self.guess_T = float(guess) / self.x_normal
            elif key == "amp":
                self.guess_amp = float(guess) / self.y_normal
            elif key == "offset":
                self.offset = float(guess) / self.y_normal
            else:
                raise Exception(
                    f"The key '{key}' specified in 'guess' does not match a fitting parameters for this function."
                )

    def func(self, x_var, a0, a1, a2, a3, a4):
        return (self.guess_amp * a0) * (
            np.sin(0.5 * (2 * np.pi * self.guess_freq * a1) * x_var + a3)
        ) ** 2 * np.exp(-x_var / np.abs(self.guess_T * a2)) + self.offset * a4

    def generate_out_dictionary(self):
        # Output the fitting function and its parameters
        out = {
            "fit_func": lambda x_var: self.fit_type(x_var / self.x_normal, self.popt) * self.y_normal,
            "f": [self.popt[1] * self.guess_freq / self.x_normal, self.perr[1] * self.guess_freq / self.x_normal],
            "phase": [self.popt[3] % (2 * np.pi), self.perr[3] % (2 * np.pi)],
            "T": [(self.guess_T * abs(self.popt[2])) * self.x_normal, self.perr[2] * self.guess_T * self.x_normal],
            "amp": [self.popt[0] * self.guess_amp * self.y_normal, self.perr[0] * self.guess_amp * self.y_normal],
            "offset": [
                self.offset * self.popt[4] * self.y_normal,
                self.perr[4] * self.offset * self.y_normal,
            ],
        }

    def print_initial_guesses(self):
        print(
            f"Initial guess:\n"
            f" f = {self.guess_freq / self.x_normal:.3f}, \n"
            f" phase = {self.guess_phase:.3f}, \n"
            f" T = {self.guess_T * self.x_normal:.3f}, \n"
            f" amplitude = {self.guess_amp * self.y_normal:.1e}, \n"
            f" offset = {self.offset * self.y_normal:.1e}"
        )

    def print_fit_results(self):
        out = self.out
        print(
            f"Fitting results:\n"
            f" f = {out['f'][0] * 1000:.3f} +/- {out['f'][1] * 1000:.3f} MHz, \n"
            f" phase = {out['phase'][0]:.3f} +/- {out['phase'][1]:.3f} rad, \n"
            f" T = {out['T'][0]:.2f} +/- {out['T'][1]:.3f} ns, \n"
            f" amplitude = {out['amp'][0]:.1e} +/- {out['amp'][1]:.1e} a.u., \n"
            f" offset = {out['offset'][0]:.1e} +/- {out['offset'][1]:.1e} a.u."
        )

    def plot_fn(self):
        plt.plot(self.x_data, self.fit_type(self.x, self.popt) * self.y_normal)
        plt.plot(
            self.x_data,
            self.y_data,
            ".",
            label=self.pi_label,
        )
        plt.legend(loc="upper right")