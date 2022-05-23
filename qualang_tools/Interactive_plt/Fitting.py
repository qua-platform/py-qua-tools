from fit_decay_sine import *
from fit_transmission_resonator_spectroscopy import *
from fit_linear import *
from fit_reflection_resonator_spectroscopy import *
from fit_phase_resonator_spectroscopy import *
import itertools
import json
import matplotlib.pyplot as plt


class Fitting:
    def __init__(self):
        pass

    def linear(self, x, y):
        fit_function = fit_linear(x, y)
        return fit_function

    def decay_sine(self, x, y):
        fit_function = fit_decay_sine(x, y)
        return fit_function

    def transmitted_lorenzian(self, x, y):
        fit_function = fit_transmission(x, y)
        return fit_function

    def reflected_lorenzian(self, x, y):
        fit_function = fit_reflection(x, y)
        return fit_function

    def phase(self, x, y):
        fit_function = fit_phase(x, y)
        return fit_function


class Save:
    def __init__(self):
        pass

    def save_params(self, x, y, fit_function, id):
        fit_func = fit_function
        fit_params = dict(itertools.islice(fit_function.items(), 1, len(fit_function)))
        fit_params['x'] = x.tolist()
        fit_params['y_data'] = y.tolist()
        fit_params['y_fit'] = fit_func["fit_func"](x).tolist()
        json_object = json.dumps(fit_params)
        with open(f"data_fit_{id}.json", "w") as outfile:
            outfile.write(json_object)


class Open:
    def __init__(self):
        pass

    def open_saved_params(self, file):
        f = open(file)
        data = json.load(f)
        return data

    def print_params(self, data):
        for key, value in data.items():
            print("{} = {}".format(key, value))


class Plot:
    def __init__(self):
        pass

    def plot(self, x, ydata, yfit, xlabel, ylabel):
        plt.plot(x, ydata, 'b.')
        plt.plot(x, yfit, 'g')
        plt.legend(['measurement', 'fit'])
        plt.xlabel(xlabel)
        plt.ylabel(ylabel)
