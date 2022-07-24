from fitting_functions import *
import itertools
import json
import matplotlib.pyplot as plt


class Fit:
    """
    This class takes care of the fitting to the measured data.
    All the fitting functions are taken from the `Fitting_functions` file.
    It includes:
        - Fitting to a linear line
        - Fitting to Ramsey experiment
        - Fitting to transmission resonator spectroscopy
        - Fitting to reflection resonator spectroscopy

    """

    def __init__(self):
        pass

    def linear(self, x, y):
        """
        Create a linear fit usinf the `fit_linear` function.
        """

        fit_function = fit_linear(x, y)
        return fit_function

    def ramsey(self, x, y):
        """
        Create a fit to Ramsey experiment using the `fit_ramsey` function.
        """

        fit_function = fit_ramsey(x, y)
        return fit_function

    def transmission_resonator_spectroscopy(self, x, y):
        """
        Create a fit to transmission resonator spectroscopy using the `fit_transmission_resonator_spectroscopy` function.
        """

        fit_function = fit_transmission_resonator_spectroscopy(x, y)
        return fit_function

    def reflection_resonator_spectroscopy(self, x, y):
        """
        Create a fit to reflection resonator spectroscopy using the `fit_reflection_resonator_spectroscopy` function.
        """

        fit_function = fit_reflection_resonator_spectroscopy(x, y)
        return fit_function


class Plot:
    """
    This class takes care of plotting the data and the fitted function.
    """

    def __init__(self):
        pass

    def plot(self, x, ydata, fit_function, xlabel=None, ylabel=None, title=None):
        """
        Plot the measured data with blue dots and the fitted function with green line.

        :param x: The data on the x axis
        :param ydata: The data on the y axis
        :param fit_function: The output of the fit function
        :param xlabel: The description of the x axis
        :param ylabel: The description of the y axis
        :param title: The title of the plot
        :return: A plot with the measured data (blue dots) and the fitted function (green line).
        """

        plt.plot(x, ydata, "b.")
        plt.plot(x, fit_function["fit_func"](x), "g")
        plt.legend(["measurement", "fit"])
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
        plt.title(title)


class Save:
    """
    This class takes care of saving the data.
    """

    def __init__(self):
        pass

    def save_params(self, x, y, fit_function, id):
        """
        Save the data as a json file

        :param x: The data on the x axis
        :param y: The data on the y axis
        :param fit_function: The output of the fit function
        :param id: The name of the saved data
        :return: A jason file with the given name, which includes all the data.
        """

        fit_func = fit_function
        fit_params = dict(itertools.islice(fit_function.items(), 1, len(fit_function)))
        fit_params["x"] = x.tolist()
        fit_params["y_data"] = y.tolist()
        fit_params["y_fit"] = fit_func["fit_func"](x).tolist()
        json_object = json.dumps(fit_params)
        with open(f"data_fit_{id}.json", "w") as outfile:
            outfile.write(json_object)


class Read:
    """
    This class takes care of reading the saved.
    """

    def __init__(self):
        pass

    def read_saved_params(self, id, print_params=False):
        """
        Read the saved json file and print the saved params if print_params=True
        :param id: The name of the json file
        :param print_params: The parameters that were saved
        :return: Dictionary with the saved data print the saved params if print_params=True
        """

        f = open(f"data_fit_{id}.json")
        data = json.load(f)
        if print_params:
            for key, value in data.items():
                print("{} = {}".format(key, value))
        return data
