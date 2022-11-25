"""Tools to help to handle plots from QUA programs.

Content:
    - interrupt_on_close: Allows to interrupt the execution and free the console when closing the live-plotting figure.
"""


from typing import List, Tuple
import numpy as np
from scipy import signal
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from qm.QmJob import QmJob


def plot_demodulated_data_2d(
    x,
    y,
    I,
    Q,
    x_label: str = None,
    y_label: str = None,
    title: str = None,
    amp_and_phase: bool = True,
    fig=None,
    plot_options: dict = None,
):
    """
    Plots 2D maps of either 'I' and 'Q' or the corresponding amplitude and phase in a single figure.

    :param x: 1D numpy array representing the x-axis.
    :param y: 1D numpy array representing the y-axis.
    :param I: 2D numpy array representing the 'I' quadrature.
    :param Q: 2D numpy array representing the 'Q' quadrature.
    :param x_label: name for the x-axis label.
    :param y_label: name for the y-axis label.
    :param title: title of the plot.
    :param amp_and_phase: if True, plots the amplitude [np.sqrt(I**2 + Q**2)] and phase [signal.detrend(np.unwrap(np.angle(I + 1j * Q)))] instead of I and Q.
    :param fig: a matplotlib figure. If `none` (default), will create a new one.
    :param plot_options: dictionary containing various plotting options. Defaults are ['fontsize': 14, 'cmap': `magma`, 'figsize': None].
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

    if fig is None:
        fig = plt.figure(figsize=_plot_options["figsize"])
    plt.suptitle(title, fontsize=_plot_options["fontsize"] + 2)
    ax1 = plt.subplot(211)
    plt.cla()
    plt.title(z1_label, fontsize=_plot_options["fontsize"])
    plt.pcolor(x, y, z1, cmap=_plot_options["cmap"])
    plt.ylabel(y_label, fontsize=_plot_options["fontsize"])
    plt.xticks(fontsize=_plot_options["fontsize"])
    plt.yticks(fontsize=_plot_options["fontsize"])
    plt.colorbar()
    plt.subplot(212, sharex=ax1)
    plt.cla()
    plt.title(z2_label, fontsize=_plot_options["fontsize"])
    plt.pcolor(x, y, z2, cmap=_plot_options["cmap"])
    plt.xlabel(x_label, fontsize=_plot_options["fontsize"])
    plt.ylabel(y_label, fontsize=_plot_options["fontsize"])
    plt.xticks(fontsize=_plot_options["fontsize"])
    plt.yticks(fontsize=_plot_options["fontsize"])
    plt.colorbar()
    plt.pause(0.01)
    plt.tight_layout()
    return fig


def plot_demodulated_data_1d(
    x: np.ndarray,
    I: np.ndarray,
    Q: np.ndarray,
    x_label: str = None,
    title: str = None,
    amp_and_phase: bool = True,
    fig=None,
    plot_options: dict = None,
):
    """
    Plots 1D graphs of either 'I' and 'Q' or the corresponding amplitude and phase in a single figure.

    :param x: 1D numpy array representing the x-axis.
    :param I: 1D numpy array representing the 'I' quadrature.
    :param Q: 1D numpy array representing the 'Q' quadrature.
    :param x_label: name for the x-axis label.
    :param title: title of the plot.
    :param amp_and_phase: if `True` (default value), plots the amplitude [np.sqrt(I**2 + Q**2)] and phase [signal.detrend(np.unwrap(np.angle(I + 1j * Q)))] instead of I and Q.
    :param fig: a matplotlib figure. If `none` (default), will create a new one.
    :param plot_options: dictionary containing various plotting options. Defaults are ['fontsize': 14, 'color': 'b', 'marker': 'o', 'linewidth': 0, 'figsize': None].
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

    if fig is None:
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
    plt.pause(0.01)
    plt.tight_layout()
    return fig


def get_simulated_samples_by_element(
    element_name: str, job: QmJob, config: dict
) -> Tuple:
    """
    Extract the simulated samples (analog and digital) corresponding to a given element.

    :param element_name: name of the element corresponding to the samples to extract. Must be defined in the config.
    :param job: The simulated QmJob from which the samples will be extracted.
    :param config: The config file used to create the job.
    :return: Two 1D lists containing the simulated analog and digital samples for the specified element.
    """
    element = config["elements"][element_name]
    job.result_handles.wait_for_all_values()
    sample_struct = job.get_simulated_samples()
    # Analog waveforms
    if "mixInputs" in element:
        port_i = element["mixInputs"]["I"]
        port_q = element["mixInputs"]["Q"]
        analog_samples = (
            sample_struct.__dict__[port_i[0]].analog[str(port_i[1])]
            + 1j * sample_struct.__dict__[port_q[0]].analog[str(port_q[1])]
        )
    elif "singleInput" in element:
        port = element["singleInput"]["port"]
        analog_samples = sample_struct.__dict__[port[0]].analog[str(port[1])]
    else:
        analog_samples = None
    # Digital waveforms
    digital_samples = []
    if "digitalInputs" in element:

        for key in element["digitalInputs"].keys():
            port = element["digitalInputs"][key]["port"]
            digital_samples.append(
                sample_struct.__dict__[port[0]].digital[str(port[1])].astype(int)
            )
    else:
        digital_samples.append(None)

    return analog_samples, digital_samples


def plot_simulator_output(
    job: QmJob,
    config: dict,
    duration_ns: int,
    plot_axes: List[List[str]] = (()),
    qua_program=None,
):
    """
    Generate a 'plotly' plot of simulator output by elements. Note that this works only if the elements don't share the same ports.

    :param job: The simulated QmJob to plot.
    :param config: The config file used to create the job.
    :param duration_ns: the duration to plot in nanosecond.
    :param plot_axes: (Either this or 'program' have to be provided) a list of lists of elements (ex: [["qubit0", "qubit1"], ["resonator0", "resonator1"]]). Will open multiple axes, one for each list.
    :param qua_program: (Either this or 'plot_axes' have to be provided) All the elements will be plotted in their own axis.
    :return: the generated 'plotly' figure.
    """
    time_vec = np.linspace(0, duration_ns - 1, duration_ns)
    samples_struct = []
    digital_samples_struct = []
    if plot_axes == (()):
        if qua_program is not None:
            # Find the elements used in the program
            el_list = []
            for statement in qua_program.__dict__["_program"].script.body.statements:
                if (
                    statement.play.qe.name not in el_list
                    and statement.play.qe.name != ""
                ):
                    el_list.append(statement.play.qe.name)
        else:
            raise Exception(
                "If plot_axis is not provided, then the qua_program must be specified as kwargs using qua_program=."
            )
        plot_axes = [[element] for element in el_list]
    for plot_axis in plot_axes:
        samples_struct.append(
            [get_simulated_samples_by_element(pa, job, config)[0] for pa in plot_axis]
        )
        digital_samples_struct.append(
            [get_simulated_samples_by_element(pa, job, config)[1] for pa in plot_axis]
        )

    fig = go.Figure().set_subplots(rows=len(plot_axes), cols=1, shared_xaxes=True)

    plot_item = None
    for i, plot_axis in enumerate(plot_axes):
        for j, plot_item in enumerate(plot_axis):
            if samples_struct[i][j] is not None:
                if isinstance(samples_struct[i][j][0], float):
                    fig.add_trace(
                        go.Scatter(
                            x=time_vec, y=samples_struct[i][j], name=plot_item + " [V]"
                        ),
                        row=i + 1,
                        col=1,
                    )
                else:
                    fig.add_trace(
                        go.Scatter(
                            x=time_vec,
                            y=samples_struct[i][j].real,
                            name=plot_item + "- I [V]",
                        ),
                        row=i + 1,
                        col=1,
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=time_vec,
                            y=samples_struct[i][j].imag,
                            name=plot_item + "- Q [V]",
                        ),
                        row=i + 1,
                        col=1,
                    )

            for k in range(len(digital_samples_struct[i][j])):
                if digital_samples_struct[i][j][k] is not None:
                    fig.add_trace(
                        go.Scatter(
                            x=time_vec,
                            y=digital_samples_struct[i][j][k],
                            name=plot_item
                            + " - "
                            + list(
                                config["elements"][plot_item]["digitalInputs"].keys()
                            )[k]
                            + " [3.3V]",
                        ),
                        row=i + 1,
                        col=1,
                    )
        fig.get_subplot(i + 1, 1).yaxis.title.text = plot_item

    fig.get_subplot(len(plot_axes), 1).xaxis.title.text = "time [ns]"
    fig.update_layout(title="Simulated waveforms")
    return fig


def interrupt_on_close(figure, current_job):
    """
    Allows to interrupt the execution and free the console when closing the live-plotting figure.

    :param figure: the python figure instance corresponding to the live-plotting figure.
    :param current_job: a ``QmJob`` object (see QM Job API) corresponding to the running job.
    """

    def on_close(event):
        print("Execution stopped by user!")
        current_job.halt()
        event.canvas.stop_event_loop()

    figure.canvas.mpl_connect("close_event", on_close)
