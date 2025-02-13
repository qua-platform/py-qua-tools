import numpy as np
import xarray as xr
import functools

from qualang_tools.characterization.two_qubit_rb.analysis.models import (
    single_exponential_decay_model,
    double_exponential_decay_model
)

from dataclasses import dataclass
from typing import Optional, Tuple
from scipy.optimize import curve_fit


@dataclass
class DoubleExponentialInitialGuess:
    A: Optional[float] = 0.25
    B: Optional[float] = 0.75
    lambda_1: Optional[float] = 0.9
    C: Optional[float] = 0.8
    lambda_2: Optional[float] = 0.9


# default initial guess
_p0 = DoubleExponentialInitialGuess()

@dataclass
class DoubleExponentialFit:
    """
    Fitted parameters of a single or double-exponential decay.

    Parameters:
    - A: Offset.
    - A_err: Standard error of A.
    - C: Amplitude.
    - C_err: Standard error of C.
    - lambda_2: Decay constant.
    - lambda_2_err: Standard error of lambda_1.
    - B: Optional second amplitude (for double-exponential fits).
    - B_err: Standard error of B (if applicable).
    - lambda_1: Optional second decay constant (for double-exponential fits).
    - lambda_1_err: Standard error of lambda_2 (if applicable).
    """

    A: float
    A_err: float

    C: float
    C_err: float
    lambda_2: float
    lambda_2_err: float

    B: Optional[float] = None
    B_err: Optional[float] = None
    lambda_1: Optional[float] = None
    lambda_1_err: Optional[float] = None

    @property
    def is_double_exponential(self):
        return not (self.C and self.lambda_2)

    def sample(self, m: np.ndarray, num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        x_fit = np.linspace(m[0], m[-1], num_points)
        if self.is_double_exponential:
            y_fit = double_exponential_decay_model(x_fit, self.A, self.B, self.lambda_1, self.C, self.lambda_2)
        else:
            y_fit = single_exponential_decay_model(x_fit, self.A, self.C, self.lambda_2)

        return x_fit, y_fit



@dataclass
class TwoQubitRbFit:
    ground_state_fit: Optional[DoubleExponentialFit]
    leakage_fit: Optional[DoubleExponentialFit]


def fit_to_single_exponential(circuit_depths, data: xr.DataArray,
                              p0: Optional[DoubleExponentialInitialGuess] = None) -> DoubleExponentialFit:
    """
    Fits the RB data to the single-exponential model A + Bλ₁ᵐ.

    Args:
        data (xr.DataArray): The RB data, with `circuit_depths` as the x-axis.

    Returns:
        DoubleExponentialFit: The fitted parameters along with their standard errors.
    """
    if p0 is None:
        p0 = [_p0.A, _p0.B, _p0.lambda_1]

    popt, pcov = curve_fit(
        f=single_exponential_decay_model,
        xdata=circuit_depths,
        ydata=data,
        p0=p0,
        maxfev=10000
    )

    perr = np.sqrt(np.diag(pcov))

    return DoubleExponentialFit(
        A=popt[0], A_err=perr[0],
        C=popt[1], C_err=perr[1],
        lambda_2=popt[2], lambda_2_err=perr[2]
    )

def fit_to_double_exponential(data: xr.DataArray, lambda_1: Optional[float] = None,
                              p0: Optional[DoubleExponentialInitialGuess] = None) -> DoubleExponentialFit:
    """
    Fits the RB data to the double-exponential model A + Bλ₁ᵐ + Cλ₂ᵐ.

    Parameters:
        data (np.ndarray): Probability of recovering to |00> as a function of circuit depths.
        lambda_1 (float, optional): If provided, lambda_1 is fixed and not fitted.

    Returns:
        DoubleExponentialFit: The fitted parameters along with their standard errors.
    """

    if lambda_1 is not None:
        f = functools.partial(double_exponential_decay_model, lambda_1=lambda_1)
        if p0 is None:
            p0 = [_p0.A, _p0.B, _p0.C, _p0.lambda_2]
    else:
        f = double_exponential_decay_model
        if p0 is None:
            p0 = [_p0.A, _p0.B, _p0.lambda_1, _p0.C, _p0.lambda_2]

    popt, pcov = curve_fit(
        f=f,
        xdata=data.circuit_depths,
        ydata=data,
        p0=p0,
        maxfev=10000
    )

    perr = np.sqrt(np.diag(pcov))  # Extract standard errors

    if lambda_1 is not None:
        lambda_1_err = None
    else:
        lambda_1, lambda_1_err = popt[3], perr[3]

    return DoubleExponentialFit(
        A=popt[0], A_err=perr[0],
        B=popt[1], B_err=perr[1],
        lambda_1=lambda_1, lambda_1_err=lambda_1_err,
        C=popt[-2], C_err=perr[-2],
        lambda_2=popt[-1], lambda_2_err=perr[-1]
    )
