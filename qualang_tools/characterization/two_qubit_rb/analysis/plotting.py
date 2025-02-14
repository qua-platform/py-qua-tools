import matplotlib.pyplot as plt
import numpy as np
import xarray as xr

from typing import Optional

from matplotlib.figure import Figure


def plot_results(
    x_data: np.ndarray,
    y_data: np.ndarray,
    y_err_data: np.ndarray,
    x_fit: np.ndarray,
    y_fit: np.ndarray,
    fidelity: Optional[float] = None
) -> Figure:
    """
    Plots the RB fidelity as a function of circuit depth, including a fit to an exponential decay model.
    The fitted curve is overlaid with the raw data points, and error bars are included.
    """
    fig = plt.figure()
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

    return fig


def plot_two_qubit_state_distribution(data: xr.Dataset) -> Figure:
    """
    Plot how the two-qubit state is distributed as a function of circuit-depth on average.
    """
    fig = plt.figure()

    plt.plot(
        data.circuit_depth,
        (data.state == 0).all(dim="qubit").mean(dim="average").mean(dim="repeat").data,
        label=r"$|00\rangle$",
        marker=".",
        color="c",
        linewidth=3,
    )
    plt.plot(
        data.circuit_depth,
        (data.state.sel(qubit=["control", "target"]) == [0, 1]).all("qubit").mean(dim=["average", "repeat"]).data,
        label=r"$|01\rangle$",
        marker=".",
        color="b",
        linewidth=1,
    )
    plt.plot(
        data.circuit_depth,
        (data.state.sel(qubit=["control", "target"]) == [1, 0]).all("qubit").mean(dim=["average", "repeat"]).data,
        label=r"$|10\rangle$",
        marker=".",
        color="y",
        linewidth=1,
    )
    plt.plot(
        data.circuit_depth,
        (data.state == 1).all(dim="qubit").mean(dim="average").mean(dim="repeat").data,
        label=r"$|11\rangle$",
        marker=".",
        color="r",
        linewidth=1,
    )
    if (data.state > 1).any():
        plt.plot(
            data.circuit_depth,
            (data.state > 1).any(dim="qubit").mean(dim="average").mean(dim="repeat").data,
            label=r"Leakage",
            marker=".",
            color="k",
            linewidth=1,
        )

    plt.axhline(0.25, color="grey", linestyle="--", linewidth=2, label="2Q mixed-state")

    plt.xlabel("Circuit Depth")
    plt.ylabel(r"Probability to recover to a given state")
    plt.title("2Q State Distribution vs. Circuit Depth")
    plt.legend(framealpha=0, title=r"2Q State $\mathbf{|q_cq_t\rangle}$", title_fontproperties={"weight": "bold"})
    plt.show()

    return fig