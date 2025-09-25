import numpy as np
import matplotlib.pyplot as plt
from typing import List, Tuple
from scipy.optimize import minimize
from scipy.optimize import curve_fit


def single_exp_decay(t: np.ndarray, amp: float, tau: float) -> np.ndarray:
    """Single exponential decay without offset

    Args:
        t (array): Time points
        amp (float): Amplitude of the decay
        tau (float): Time constant of the decay

    Returns:
        array: Exponential decay values
    """
    return amp * np.exp(-t / tau)


def sequential_exp_fit(
    t: np.ndarray,
    y: np.ndarray,
    start_fractions: List[float],
    fixed_taus: List[float] = None,
    a_dc: float = None,
    verbose: bool = 1,
) -> Tuple[List[Tuple[float, float]], float, np.ndarray]:
    """
    Fit multiple exponentials sequentially by:
    1. First fit a constant term from the tail of the data
    2. Fit the longest time constant using the latter part of the data
    3. Subtract the fit
    4. Repeat for faster components

    Args:
        t (array): Time points in nanoseconds, representing the time resolution of the pulse.
        y (array): Amplitude values of the pulse in volts.
        start_fractions (list): List of fractions (0 to 1) indicating where to start fitting each component. Choice is user defined.
        fixed_taus (list, optional): Fixed tau values (in nanoseconds) for each exponential component.
                                   If provided, only amplitudes are fitted, taus are constrained.
                                   Must have same length as start_fractions.
        a_dc (float, optional): Fixed constant term. If provided, the constant term is not fitted.
        verbose (int): Whether to print detailed fitting information (0: no prints, 1: prints only initial and final parameters, 2: prints all the fitting information)

    Returns:
        tuple: (components, a_dc, residual) where:
            - components: List of (amplitude, tau) pairs for each fitted component
            - a_dc: Fitted constant term or the fixed constant term
            - residual: The difference between the measured data and the fitted curve after subtracting all exponential components.
    """

    components = []  # List to store (amplitude, tau) pairs
    t_offset = t - t[0]  # Make time start at 0

    # Find the flat region in the tail by looking at local variance
    window = max(5, len(y) // 20)  # Window size by dividing signal into 20 equal pieces or at least 5 points
    rolling_var = np.array([np.var(y[i : i + window]) for i in range(len(y) - window)])
    # Find where variance drops below threshold, indicating flat region
    var_threshold = np.mean(rolling_var) * 0.1  # 10% of mean variance
    if a_dc is None:
        try:
            flat_start = np.where(rolling_var < var_threshold)[0][-1]
            # Use the flat region to estimate constant term
            a_dc = np.mean(y[flat_start:])
        except IndexError:
            print("No flat region found, using last point of the signal as constant term")
            a_dc = y[-1]

    if verbose:
        print(f"\nFitted constant term: {a_dc:.3e}")

    y_residual = y.copy() - a_dc

    for i, start_frac in enumerate(start_fractions):
        # Calculate start index for this component
        start_idx = int(len(t) * start_frac)
        if verbose:
            print(f"\nFitting component {i + 1} using data from t = {t[start_idx]:.1f} ns (fraction: {start_frac:.3f})")

        # Fit current component
        try:
            # Prepare fitting parameters based on whether tau is fixed
            if fixed_taus is not None:
                # Use fixed tau - only fit amplitude using lambda
                tau_fixed = fixed_taus[i]
                p0 = [y_residual[start_idx]]  # Only amplitude initial guess
                if verbose:
                    print(f"Using fixed tau = {tau_fixed:.3f} ns")

                # Perform the fit on the current interval
                t_fit = t_offset[start_idx:]
                y_fit = y_residual[start_idx:]
                popt, _ = curve_fit(lambda t, amp: single_exp_decay(t, amp, tau_fixed), t_fit, y_fit, p0=p0)

                # Store the components
                amp = popt[0]
                tau = tau_fixed
            else:
                # Fit both amplitude and tau (original behavior)
                p0 = [y_residual[start_idx], t_offset[start_idx] / 3]  # amplitude  # tau

                # Set bounds for the fit
                bounds = (
                    [-np.inf, 0.1],
                    # lower bounds: amplitude can be negative, tau must be positive (0.1 ns is arbitrary)
                    [np.inf, np.inf],  # upper bounds
                )

                # Perform the fit on the current interval
                t_fit = t_offset[start_idx:]
                y_fit = y_residual[start_idx:]
                popt, _ = curve_fit(single_exp_decay, t_fit, y_fit, p0=p0, bounds=bounds)

                # Store the components
                amp, tau = popt

            components.append((amp, tau))
            if verbose:
                tau_status = "(fixed)" if fixed_taus is not None else ""
                print(f"Found component: amplitude = {amp:.3e}, tau = {tau:.3f} ns {tau_status}")

            # Subtract this component from the entire signal
            y_residual -= amp * np.exp(-t_offset / tau)

        except (RuntimeError, ValueError) as e:
            if verbose:
                print(f"Warning: Fitting failed for component {i + 1}: {e}")
            break

    return components, a_dc, y_residual


def optimize_start_fractions(t, y, start_fractions, bounds_scale=0.5, fixed_taus=None, a_dc=None, verbose=1):
    """
    Optimize the start_fractions by minimizing the RMS between the data and the fitted sum
    of exponentials using scipy.optimize.minimize.

    Args:
        t (array): Time points in nanoseconds, representing the time resolution of the pulse.
        y (array): Amplitude values of the pulse in volts.
        start_fractions (list): Initial guess for start fractions. Choice is user defined.
        bounds_scale (float): Scale factor for bounds around start fractions (0.5 means ±50%)
        fixed_taus (list, optional): Fixed tau values (in nanoseconds) for each exponential component.
                                   If provided, only amplitudes are fitted, taus are constrained.
                                   Must have same length as start_fractions.
        a_dc (float, optional): Constant term. If not provided, the constant term is fitted from
                                the tail of the data.
        verbose (int): Whether to print detailed fitting information (0: no prints, 1: prints only initial and final parameters, 2: prints all the fitting information)

    Returns:
        tuple: (success, best_fractions, best_components, best_dc, best_rms)
    """
    # Validate fixed_taus parameter
    if fixed_taus is not None:
        if len(fixed_taus) != len(start_fractions):
            raise ValueError("fixed_taus must have the same length as start_fractions")
        if any(tau <= 0 for tau in fixed_taus):
            raise ValueError("All fixed_taus values must be positive")

    def objective(x):
        """
        Objective function to minimize: RMS between the data and the fitted sum of
        exponentials.
        """
        # Ensure fractions are ordered in descending order
        if not np.all(np.diff(x) < 0):
            return 1e6  # Return large value if constraint is violated

        components, _, residual = sequential_exp_fit(t, y, x, fixed_taus=fixed_taus, a_dc=a_dc, verbose=verbose)
        if len(components) == len(start_fractions):
            current_rms = np.sqrt(np.mean(residual**2))
        else:
            current_rms = 1e6  # Return large value if fitting fails

        return current_rms

    # Define bounds for optimization
    bounds = []
    for start in start_fractions:
        min_val = start * (1 - bounds_scale)
        max_val = start * (1 + bounds_scale)
        bounds.append((min_val, max_val))
    if verbose > 0:
        print("\nOptimizing start_fractions using scipy.optimize.minimize...")
        print(f"Initial values: {[f'{f:.5f}' for f in start_fractions]}")
        print(f"Bounds: ±{bounds_scale * 100}% around initial values")

    # Run optimization
    result = minimize(
        objective,
        x0=start_fractions,
        bounds=bounds,
        method="Nelder-Mead",  # This method works well for non-smooth functions
        options={"disp": True, "maxiter": 200},
    )

    # Get final results
    if result.success:
        best_fractions = result.x
        components, a_dc, best_residual = sequential_exp_fit(
            t, y, best_fractions, fixed_taus=fixed_taus, a_dc=a_dc, verbose=False
        )
        best_rms = np.sqrt(np.mean(best_residual**2))
        if verbose > 0:
            print("\nOptimization successful!")
            print(f"Initial fractions: {[f'{f:.5f}' for f in start_fractions]}")
            print(f"Optimized fractions: {[f'{f:.5f}' for f in best_fractions]}")
            if fixed_taus is not None:
                print(f"Fixed taus: {[f'{tau:.3f} ns' for tau in fixed_taus]}")
            print(f"Final RMS: {best_rms:.3e}")
            print(f"Number of iterations: {result.nit}")
    else:
        if verbose > 0:
            print("\nOptimization failed. Using initial values.")
        best_fractions = start_fractions
        components, a_dc, best_residual = sequential_exp_fit(
            t, y, best_fractions, fixed_taus=fixed_taus, a_dc=a_dc, verbose=False
        )
        best_rms = np.sqrt(np.mean(best_residual**2))

    components = [(amp * np.exp(t[0] / tau), tau) for amp, tau in components]
    if verbose > 0:
        print("Optimized components [(a1, tau1), (a2, tau2)...]:")
        print(components)
    return result.success, best_fractions, components, a_dc, best_rms


def plot_fit(t_data: np.ndarray, y_data: np.ndarray, components: List[Tuple[float, float]], a_dc: float):
    """Plot exponential fit results with both linear and log scales.

    Args:
        t_data (np.ndarray): Time points in nanoseconds
        y_data (np.ndarray): Measured flux response data
        components (List[Tuple[float, float]]): List of (amplitude, tau) pairs for each fitted component
        a_dc (float): Constant term

    Returns:
        tuple: (fig, axs) where:
            - fig: Figure object
            - axs: List of axes objects
    """

    fit_text = f"a_dc = {a_dc:.3f}\n"
    y_fit = np.ones_like(t_data, dtype=float) * a_dc
    for i, (amp, tau) in enumerate(components):
        y_fit += amp * np.exp(-t_data / tau)
        fit_text += f"a{i + 1} = {amp / a_dc:.3f}, τ{i + 1} = {tau:.0f}ns\n"

    fig, axs = plt.subplots(1, 2, figsize=(12, 5))

    # First subplot - linear scale
    axs[0].plot(t_data, y_data, label="Data")
    axs[0].plot(t_data, y_fit, label="Fit")
    axs[0].text(
        0.98,
        0.5,
        fit_text,
        transform=axs[0].transAxes,
        fontsize=10,
        horizontalalignment="right",
        verticalalignment="center",
    )
    axs[0].set_xlabel("Time (ns)")
    axs[0].set_ylabel("Flux Response")
    axs[0].legend()
    axs[0].grid(True)
    axs[0].ticklabel_format(axis="x", style="sci", scilimits=(0, 0))

    # Second subplot - log scale
    axs[1].plot(t_data, y_data, label="Data")
    axs[1].plot(t_data, y_fit, label="Fit")
    axs[1].text(
        0.98,
        0.5,
        fit_text,
        transform=axs[1].transAxes,
        fontsize=10,
        horizontalalignment="right",
        verticalalignment="center",
    )
    axs[1].set_xlabel("Time (ns)")
    axs[1].set_ylabel("Flux Response")
    axs[1].set_xscale("log")
    axs[1].legend(loc="best")
    axs[1].grid(True)

    fig.tight_layout()

    return fig, axs
