import dataclasses
from typing import Tuple, Optional, Sequence, List

import numpy as np
import xarray as xr

from qualang_tools.characterization.two_qubit_rb.analysis.fitting import (
    fit_to_single_exponential,
    fit_to_double_exponential,
    TwoQubitRbFit
)
from qualang_tools.characterization.two_qubit_rb.analysis.plotting import plot_results

from qualang_tools.characterization.two_qubit_rb.analysis.fidelity import calculate_average_two_qubit_clifford_fidelity
from qualang_tools.characterization.two_qubit_rb.analysis.plotting import plot_two_qubit_state_distribution


@dataclasses.dataclass
class RBResult:
    """
    Class for analyzing and visualizing the results of a Randomized Benchmarking (RB) experiment.

    Attributes:
        circuit_depths (list[int]): List of circuit depths used in the RB experiment.
        num_repeats (int): Number of repeated sequences at each circuit depth.
        num_averages (int): Number of averages for each sequence.
        state_control (np.ndarray): Measured control-qubit states from the RB experiment.
        state_target (np.ndarray): Measured target-qubit states from the RB experiment.
    """
    circuit_depths: np.ndarray
    num_repeats: int
    num_averages: int
    state_control: np.ndarray
    state_target: np.ndarray

    def __post_init__(self):
        """
        Initializes the xarray Dataset to store the RB experiment data.
        """
        self.data = xr.Dataset(
            data_vars={"state": (["repeat", "circuit_depth", "average", "qubit"],
                       np.stack((self.state_control, self.state_target), axis=-1))},
            coords={
                "repeat": range(self.num_repeats),
                "circuit_depth": self.circuit_depths,
                "average": range(self.num_averages),
                "qubit": ["control", "target"]
            },
        )
        self.state = self.data.state


    @property
    def leakage_was_measured(self):
        return (self.state > 1).any()


    def fit(self, p0: Optional[List[float]] = None) -> TwoQubitRbFit:
        """
        Fit the two-qubit randomized benchmarking (RB) data to extract decay parameters,
        following the methodology described by Wood and Gambetta.

        The procedure depends on whether leakage data has been measured:

        - **Leakage measured:**
          The method first fits the probability of remaining in the computational subspace
          (i.e., not leaking out) to a single-exponential decay model. The resulting decay
          constant (lambda_1) is then used as a fixed parameter in a subsequent double-exponential
          fit of the ground state probability. This double-exponential model captures both the
          ground state decay and the leakage effect, as per Wood & Gambetta's Leakage Randomized
          Benchmarking protocol (LRB).

        - **Leakage not measured:**
          The method fits the ground state probability directly using a single-exponential decay
          model, as per the regular Randomized Benchmarking protocol (RB).

        Returns:
            TwoQubitRbFit: An object containing the fitted decay parameters and their uncertainties.

        References:
            Wood, C.J. and Gambetta, J.M., 2018. Quantification and characterization of leakage errors.
            Physical Review A, 97(3), p.032306.
        """
        leakage_fit = None

        probability_of_remaining_in_computational_subspace, _ = self.probability_of_remaining_in_computational_subspace()
        probability_of_ground_state, _ = self.probability_of_ground_state()

        if self.leakage_was_measured:
            leakage_fit = fit_to_single_exponential(self.circuit_depths, probability_of_remaining_in_computational_subspace)
            ground_state_fit = fit_to_double_exponential(self.circuit_depths, probability_of_ground_state, lambda_1=leakage_fit.lambda_1, p0=p0)

        else:
            ground_state_fit = fit_to_single_exponential(self.circuit_depths, probability_of_ground_state, p0=p0)

        return TwoQubitRbFit(
            ground_state_fit=ground_state_fit,
            leakage_fit=leakage_fit,
        )

    def get_fidelity(self, fit: Optional[TwoQubitRbFit] = None):
        if fit is None:
            fit = self.fit()

        return calculate_average_two_qubit_clifford_fidelity(fit)

    def probability_of_ground_state(self) -> Tuple[xr.DataArray, xr.DataArray]:
        """
        Returns:
            tuple:
                xarray.DataArray: The probability of measuring the ground state |00> for each circuit depth.
                xarray.DataArray: The standard deviation of the probability along the randomization axis.
        """
        ground_state = (self.state == 0).all(dim="qubit")
        ground_state_probability = ground_state.mean(("repeat", "average"))
        ground_state_probability_err = ground_state.mean("average").std("repeat")

        return ground_state_probability, ground_state_probability_err


    def probability_of_remaining_in_computational_subspace(self) -> Tuple[xr.DataArray, xr.DataArray]:
        """
        Returns:
            tuple:
                xarray.DataArray: The probability of measuring the two-qubit state in the
                computational subspace, i.e., the probability of measuring |00>, |01>, |10>, or |11>.
                xarray.DataArray: The standard deviation of the probability along the randomization axis.
        """
        individual_computational_subspace_states = [0, 1]
        computational_subspace_state = self.state.isin(individual_computational_subspace_states).all(dim="qubit")
        computational_subspace_state_probability = computational_subspace_state.mean(("repeat", "average"))
        computational_subspace_state_probability_err = computational_subspace_state.mean("average").std("repeat")

        return computational_subspace_state_probability, computational_subspace_state_probability_err


    def plot(self, fit: Optional[TwoQubitRbFit] = None):
        if fit is None:
            fit = self.fit()

        y_data, _ = self.probability_of_ground_state()
        fidelity = self.get_fidelity(fit)
        x_fit, y_fit = fit.ground_state_fit.sample(self.circuit_depths)
        plot_results(
            x_data=self.circuit_depths,
            y_data=y_data.data,
            y_err_data=(self.data == 0).all(dim="qubit").mean(dim="average").std(dim="repeat").state.data,
            x_fit=x_fit,
            y_fit=y_fit,
            fidelity=fidelity
        )

    def plot_two_qubit_state_distribution(self):
        """
        Plot how the two-qubit state is distributed as a function of circuit-depth on average.
        """
        plot_two_qubit_state_distribution(self.data)
