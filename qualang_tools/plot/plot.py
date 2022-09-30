"""Tools to help handling plots from QUA programs.

Content:
    - interrupt_on_close: Allows to interrupt the execution and free the console when closing the live-plotting figure.
"""


from typing import List
import numpy as np
import plotly.graph_objects as go
from matplotlib import pyplot as plt
from qm.QmJob import QmJob


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
    :return:
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
    :return: None.
    """

    def on_close(event):
        print("Execution stopped by user!")
        current_job.halt()
        event.canvas.stop_event_loop()

    figure.canvas.mpl_connect("close_event", on_close)
