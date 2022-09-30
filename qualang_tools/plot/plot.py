"""Tools to help to handle plots from QUA programs.

Content:
    - interrupt_on_close: Allows to interrupt the execution and free the console when closing the live-plotting figure.
"""


from typing import List
import numpy as np
from scipy import signal
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from qm.QmJob import QmJob


def plot_amplitude_and_phase_2d(
    x,
    y,
    I,
    Q,
    amp_and_phase: bool = True,
    x_label: str = None,
    y_label: str = None,
    title: str = None,
    plot_options: dict = None,
):
    """
    Plot 2D maps of either 'I' and 'Q' or the corresponding amplitude and phase in a single figure.

    :param x: 1D numpy array representing the x-axis.
    :param y: 1D numpy array representing the y-axis.
    :param I: 2D numpy array representing the 'I' quadrature.
    :param Q: 2D numpy array representing the 'Q' quadrature.
    :param amp_and_phase: if True, plots the amplitude [np.sqrt(I**2 + Q**2)] and phase [signal.detrend(np.unwrap(np.angle(I + 1j * Q)))] instead of I and Q.
    :param x_label: name for the x-axis label.
    :param y_label: name for the y-axis label.
    :param title: title of the plot.
    :param plot_options: dictionary containing various plotting options ['fontsize', 'cmap', 'figsize'].
    :return: the matplotlib figure object.
    """
    _plot_options = {
        "fontsize": 14,
        "cmap": "magma",
        "figsize": None,
    }
    if plot_options is not None:
        for key in plot_options:
            if key in _plot_options.keys():
                _plot_options[key] = plot_options[key]
            else:
                raise ValueError(
                    f"The key {key} in 'plot_options' doesn't exists. The available options are {[option for option in _plot_options.keys()]}"
                )
    if amp_and_phase:
        z1 = np.sqrt(I**2 + Q**2)
        z2 = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))
        z1_label = "Amplitude [a.u.]"
        z2_label = "Phase [rad]"
    else:
        z1 = I
        z2 = Q
        z1_label = "I [a.u.]"
        z2_label = "Q [a.u.]"

    fig = plt.figure(figsize=_plot_options["figsize"])
    plt.suptitle(title, fontsize=_plot_options["fontsize"] + 2)
    ax1 = plt.subplot(211)
    plt.cla()
    plt.title(z1_label)
    plt.pcolor(x, y, z1, cmap=_plot_options["cmap"])
    plt.ylabel(y_label, fontsize=_plot_options["fontsize"])
    plt.xticks(fontsize=_plot_options["fontsize"])
    plt.yticks(fontsize=_plot_options["fontsize"])
    plt.colorbar()
    plt.subplot(212, sharex=ax1)
    plt.cla()
    plt.title(z2_label)
    plt.pcolor(x, y, z2, cmap=_plot_options["cmap"])
    plt.xlabel(x_label, fontsize=_plot_options["fontsize"])
    plt.ylabel(y_label, fontsize=_plot_options["fontsize"])
    plt.xticks(fontsize=_plot_options["fontsize"])
    plt.yticks(fontsize=_plot_options["fontsize"])
    plt.colorbar()
    plt.tight_layout()
    return fig


def plot_amplitude_and_phase_1d(
    x: np.ndarray,
    I: np.ndarray,
    Q: np.ndarray,
    amp_and_phase: bool = True,
    x_label: str = None,
    title: str = None,
    plot_options: dict = None,
):
    """
    Plot 1D graphs of either 'I' and 'Q' or the corresponding amplitude and phase in a single figure.

    :param x: 1D numpy array representing the x-axis.
    :param I: 1D numpy array representing the 'I' quadrature.
    :param Q: 1D numpy array representing the 'Q' quadrature.
    :param amp_and_phase: if True, plots the amplitude [np.sqrt(I**2 + Q**2)] and phase [signal.detrend(np.unwrap(np.angle(I + 1j * Q)))] instead of I and Q.
    :param x_label: name for the x-axis label.
    :param title: title of the plot.
    :param plot_options: dictionary containing various plotting options ['fontsize', 'color', 'marker', 'linewidth', 'figsize'].
    :return: the matplotlib figure object.
    """
    _plot_options = {
        "fontsize": 14,
        "color": "b",
        "marker": "o",
        "linewidth": 0,
        "figsize": None,
    }
    if plot_options is not None:
        for key in plot_options:
            if key in _plot_options.keys():
                _plot_options[key] = plot_options[key]
            else:
                raise ValueError(
                    f"The key '{key}' in 'plot_options' doesn't exists. The available options are {[option for option in _plot_options.keys()]}"
                )

    if amp_and_phase:
        y1 = np.sqrt(I**2 + Q**2)
        y2 = signal.detrend(np.unwrap(np.angle(I + 1j * Q)))
        y1_label = "Amplitude [a.u.]"
        y2_label = "Phase [rad]"
    else:
        y1 = I
        y2 = Q
        y1_label = "I [a.u.]"
        y2_label = "Q [a.u.]"

    fig = plt.figure(figsize=_plot_options["figsize"])
    plt.suptitle(title, fontsize=_plot_options["fontsize"] + 2)
    ax1 = plt.subplot(211)
    plt.cla()
    plt.plot(
        x,
        y1,
        color=_plot_options["color"],
        marker=_plot_options["marker"],
        linewidth=_plot_options["linewidth"],
    )
    plt.ylabel(y1_label, fontsize=_plot_options["fontsize"])
    plt.xticks(fontsize=_plot_options["fontsize"])
    plt.yticks(fontsize=_plot_options["fontsize"])
    plt.subplot(212, sharex=ax1)
    plt.cla()
    plt.plot(
        x,
        y2,
        color=_plot_options["color"],
        marker=_plot_options["marker"],
        linewidth=_plot_options["linewidth"],
    )
    plt.xlabel(x_label, fontsize=_plot_options["fontsize"])
    plt.ylabel(y2_label, fontsize=_plot_options["fontsize"])
    plt.xticks(fontsize=_plot_options["fontsize"])
    plt.yticks(fontsize=_plot_options["fontsize"])
    plt.tight_layout()
    return fig


def plot_channel(ax, data: np.ndarray, title: str):
    """
    Plot data from one channel to a given axis.

    :param ax: valid matplotlib.pyplot axis .
    :param data: 1D array containing the data to be plotted, can be real or complex.
    :param title: title of the plot.

    """
    if data.dtype == np.complex:
        ax.plot(data.real, label="Real part")
        ax.plot(data.imag, label="Imaginary part")
        ax.legend(loc="upper right")
    else:
        ax.plot(data)
    ax.set_title(title)
    ax.set_ylim((-0.6, 0.6))


def get_simulated_samples_by_element(element_name: str, job: QmJob, config: dict):
    """
    Extract the simulated samples corresponding to a given element.

    :param element_name: name of the element corresponding to the samples to extract. Must be defined in the config.
    :param job: The simulated QmJob from which the samples will be extracted.
    :param config: The config file used to create the job.
    :return: 1D complex array containing the simulated samples for the specified element.
    """
    element = config["elements"][element_name]
    sample_struct = job.get_simulated_samples()
    if "mixInputs" in element:
        port_i = element["mixInputs"]["I"]
        port_q = element["mixInputs"]["Q"]
        samples = (
            sample_struct.__dict__[port_i[0]].analog[str(port_i[1])]
            + 1j * sample_struct.__dict__[port_q[0]].analog[str(port_q[1])]
        )
    else:
        port = element["singleInput"]["port"]
        samples = sample_struct.__dict__[port[0]].analog[str(port[1])]
    return samples


def plot_simulator_output(
    plot_axes: List[List[str]], job: QmJob, config: dict, duration_ns: int
):
    """
    generate a plot of simulator output by elements

    :param plot_axes: a list of lists of elements. Will open
    multiple axes, one for each list.
    :param job: The simulated QmJob to plot.
    :param config: The config file used to create the job.
    :param duration_ns: the duration to plot in nanosecond.
    """
    time_vec = np.linspace(0, duration_ns - 1, duration_ns)
    samples_struct = []
    for plot_axis in plot_axes:
        samples_struct.append(
            [get_simulated_samples_by_element(pa, job, config) for pa in plot_axis]
        )

    fig = go.Figure().set_subplots(rows=len(plot_axes), cols=1, shared_xaxes=True)

    for i, plot_axis in enumerate(plot_axes):
        for j, plot_item in enumerate(plot_axis):
            if samples_struct[i][j].dtype == np.float:
                fig.add_trace(
                    go.Scatter(x=time_vec, y=samples_struct[i][j], name=plot_item),
                    row=i + 1,
                    col=1,
                )
                print(samples_struct[i][j])
            else:
                fig.add_trace(
                    go.Scatter(
                        x=time_vec, y=samples_struct[i][j].real, name=plot_item + " I"
                    ),
                    row=i + 1,
                    col=1,
                )
                fig.add_trace(
                    go.Scatter(
                        x=time_vec, y=samples_struct[i][j].imag, name=plot_item + " Q"
                    ),
                    row=i + 1,
                    col=1,
                )
    fig.update_xaxes(title="time [ns]")
    return fig


def plot_ar_attempts(res_handles, qubits: List[int], attempts_data: str, **hist_kwargs):
    """
    Plot the histogram of the number of attempts necessary to perform active reset.

    :param res_handles: results handle containing the number of attempts.
    :param attempts_data: base name for the data containing the number of attempts for each qubit (ex: 'AR_attempts_qb').
    :param qubits: list of the qubit numbers involved in the experiment as defined in the config (ex: [0, 2, 4]).
    :param hist_kwargs: arguments to be passed to the 'hist' plot.
    """
    ar_data = {
        q: res_handles.get(attempts_data + str(q)).fetch_all()["value"] for q in qubits
    }
    fig, axes = plt.subplots(1, len(qubits), sharex="all", figsize=(14, 4))
    for i, q in enumerate(qubits):
        ax = axes[i]
        ax.hist(ar_data[q], **hist_kwargs)
        ax.set_title(f"q = {q}")
        ax.set_ylabel("prob.")
        ax.set_xlabel("no. of attempts")
    fig.tight_layout()


def interrupt_on_close(figure, current_job):
    """
    Allows to interrupt the execution and free the console when closing the live-plotting figure.

    :param figure: the python figure instance correponding to the live-plotting figure.
    :param current_job: a ``QmJob`` object (see QM Job API) corresponding to the running job.
    """

    def on_close(event):
        print("Execution stopped by user!")
        current_job.halt()
        event.canvas.stop_event_loop()

    figure.canvas.mpl_connect("close_event", on_close)
