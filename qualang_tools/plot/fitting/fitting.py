from .fit_classes import T1
from .fit_classes import Linear
from .fit_classes import Ramsey
from .fit_classes import RamseyWithGaussianEnvelope
from .fit_classes import Lorentzian
from .fit_classes import DoubleLorentzian
from .fit_classes import TripleLorentzian
from .fit_classes import Absolute
from .fit_classes import Rabi
from .fit_classes import ReflectionResonatorSpectroscopy
from .fit_classes import TransmissionResonatorSpectroscopy
from .fit_classes import ResonatorFrequencyVsFlux

from typing import List, Union
import numpy as np


class Fitting:

    @staticmethod
    def T1(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return T1(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def linear(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return Linear(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def ramsey(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return Ramsey(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def ramsey_with_gaussian_envelope(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return RamseyWithGaussianEnvelope(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def lorentzian(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return Lorentzian(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def double_lorentzian(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return DoubleLorentzian(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def triple_lorentzian(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return TripleLorentzian(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def absolute(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return Absolute(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def rabi(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return Rabi(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def reflection_resonator_spectroscopy(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return ReflectionResonatorSpectroscopy(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def transmission_resonator_spectroscopy(
            x_data: Union[np.ndarray, List[float]],
            y_data: Union[np.ndarray, List[float]],
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return TransmissionResonatorSpectroscopy(x_data, y_data, guess, verbose, plot, save)

    @staticmethod
    def resonator_frequency_vs_flux(
            frequency: Union[np.ndarray, List[float]],
            flux: Union[np.ndarray, List[float]],
            data: np.ndarray,
            guess=None,
            verbose=False,
            plot=False,
            save=False
    ):
        return ResonatorFrequencyVsFlux(frequency, flux, data, guess, verbose, plot, save)

