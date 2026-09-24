"""Shared helpers for the bakery-beyond-clockcycle-resolution examples."""

from __future__ import annotations

import inspect

import numpy as np
from scipy.optimize import curve_fit


def gaussian_i(amp: float, n_samples: int, sampling_rate: float) -> list[float]:
    """Subtracted Gaussian of ``n_samples`` at ``sampling_rate``, sigma = length/5."""
    dt_ns = 1e9 / sampling_rate
    t = np.arange(n_samples, dtype=float) * dt_ns
    length_ns = n_samples * dt_ns
    sigma_ns = length_ns / 5.0
    center = (length_ns - dt_ns) / 2.0
    wf = np.exp(-((t - center) ** 2) / (2.0 * sigma_ns**2))
    wf = (wf - wf.min()) / (wf.max() - wf.min()) * amp
    return wf.tolist()


def gaussian_model(t: np.ndarray, nu: float, sigma: float, amp: float) -> np.ndarray:
    """Outputs the same array as gaussian_i. Inputs for fitting parameters."""
    raw = np.exp(-((t - nu) ** 2) / (2.0 * sigma**2))
    return (raw - raw.min()) / (raw.max() - raw.min()) * amp


def index_of(duration_ns: np.ndarray, target_ns: float) -> int:
    """Index of the sweep point in ``duration_ns`` closest to ``target_ns``."""
    return int(np.argmin(np.abs(duration_ns - target_ns)))


def time_from_center(samples: np.ndarray, snap_to_1ns: bool = False) -> np.ndarray:
    """Time axis (ns) with 0 at the amplitude centroid of ``samples``.

    ``snap_to_1ns`` rounds the centroid to the nearest integer sample, so
    points that only differ by a sub-ns duration line up on the same grid.
    """
    t = np.arange(len(samples), dtype=float)
    weights = np.abs(samples)
    center = np.sum(t * weights) / np.sum(weights)
    if snap_to_1ns:
        center = np.round(center)
    return t - center


def check_dac(model, samples, p0, tolerance: float = 0.005, dac_bits: int = 15, label: str = "") -> bool:
    """DAC-round ``samples`` and check they still fit ``model`` at ``p0``.

    ``model(t, *params)`` is the analytical function for the ideal waveform
    (e.g. a Gaussian); ``p0`` is its intended parameters. Rounds ``samples``
    to ``dac_bits`` bits (default 15, a 16-bit signed DAC), fits ``model``
    to the rounded data, and warns if any fitted parameter deviates from
    its intended value in ``p0`` by more than ``tolerance`` (fractional).
    Returns True iff every parameter is within tolerance.
    """
    t = np.arange(len(samples), dtype=float)
    dac_rounded = np.round(np.asarray(samples, dtype=float) * 2**dac_bits) / 2**dac_bits
    popt, _ = curve_fit(model, t, dac_rounded, p0=p0)
    tag = f" [{label}]" if label else ""
    pars = list(inspect.signature(model).parameters)[1:]  # drop t
    at_least_one_param_out_of_tolerance = False
    for i, (fit, intended) in enumerate(zip(popt, p0)):
        deviation = abs(fit - intended) / abs(intended) if intended else float("inf")
        if deviation > tolerance:
            if not at_least_one_param_out_of_tolerance:
                print('#' + '-' * 78 + '#')
                print(f"WARNING: DAC-rounded waveform{tag} deviates from intended parameters:")
            print(
                f"{pars[i]} fit={fit:.5g} intended={intended:.5g} "
                f"deviates {deviation * 100:.2f}% (tolerance {tolerance * 100:.2f}%)"
            )
            at_least_one_param_out_of_tolerance = True
        if i == len(popt) - 1 and at_least_one_param_out_of_tolerance:
            print('#' + '-' * 78 + '#')
    return not at_least_one_param_out_of_tolerance
