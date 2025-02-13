import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from typing import Optional


def plot_results(
    x_data: np.ndarray,
    y_data: np.ndarray,
    y_err_data: np.ndarray,
    x_fit: np.ndarray,
    y_fit: np.ndarray,
    fidelity: Optional[float] = None
):
    """
    Plots the RB fidelity as a function of circuit depth, including a fit to an exponential decay model.
    The fitted curve is overlaid with the raw data points, and error bars are included.
    """
    plt.figure()
    plt.errorbar(
        x_data, y_data, yerr=y_err_data, fmt=".", capsize=2, elinewidth=0.5, color="blue",
        label="Experimental Data"
    )

    plt.plot(
        x_fit, y_fit, color="red", linestyle="--",
        label="Exponential Fit"
    )

    if fidelity is not None:
        plt.text(
            x=0.5, y=0.95,
            s=f"2Q Clifford Fidelity = {fidelity * 100:.2f}%",
            horizontalalignment="center",
            verticalalignment="top",
            fontdict={"fontsize": "large", "fontweight": "bold"},
            transform=plt.gca().transAxes,
        )

    plt.xlabel("Circuit Depth")
    plt.ylabel(r"Probability to recover to $|00\rangle$")
    plt.title("2Q Randomized Benchmarking")
    plt.legend(framealpha=0)
    plt.show()


def plot_two_qubit_state_distribution(data: xr.Dataset):
    """
    Plot how the two-qubit state is distributed as a function of circuit-depth on average.
    """
    plt.plot(
        data.circuit_depths,
        (data.state.sel(qubit="control") == 0 and data.state.sel(qubit="target") == 0).mean(dim="average").mean(dim="repeat").data,
        label=r"$|00\rangle$",
        marker=".",
        color="c",
        linewidth=3,
    )
    plt.plot(
        data.circuit_depths,
        (data.state.sel(qubit="control") == 0 and data.state.sel(qubit="target") == 1).mean(dim="average").mean(dim="repeat").data,
        label=r"$|01\rangle$",
        marker=".",
        color="b",
        linewidth=1,
    )
    plt.plot(
        data.circuit_depths,
        (data.state.sel(qubit="control") == 1 and data.state.sel(qubit="target") == 0).mean(dim="average").mean(dim="repeat").data,
        label=r"$|10\rangle$",
        marker=".",
        color="y",
        linewidth=1,
    )
    plt.plot(
        data.circuit_depths,
        (data.state.sel(qubit="control") == 1 and data.state.sel(qubit="target") == 1).mean(dim="average").mean(dim="repeat").data,
        label=r"$|11\rangle$",
        marker=".",
        color="r",
        linewidth=1,
    )
    if any(data.state.sel(qubit="control") > 1 or data.state.sel(qubit="target") > 0):
        plt.plot(
            data.circuit_depths,
            (data.state.sel(qubit="control") > 1 or data.state.sel(qubit="target") > 1).mean(dim="average").mean(dim="repeat").data,
            label=r"Leakage",
            marker=".",
            color="r",
            linewidth=1,
        )

    plt.axhline(0.25, color="grey", linestyle="--", linewidth=2, label="2Q mixed-state")

    plt.xlabel("Circuit Depth")
    plt.ylabel(r"Probability to recover to a given state")
    plt.title("2Q State Distribution vs. Circuit Depth")
    plt.legend(framealpha=0, title=r"2Q State $\mathbf{|q_cq_t\rangle}$", title_fontproperties={"weight": "bold"})
    plt.show()
