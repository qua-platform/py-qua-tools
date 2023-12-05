import matplotlib.pyplot as plt
import numpy as np


def _round_to_fixed_point_accuracy(x, accuracy=2**-15):
    return np.round(x / accuracy) * accuracy


def convert_integration_weights(integration_weights, N=100, accuracy=2**-15, plot=False):
    """
    Converts a list of integration weights, in which each sample corresponds to a clock cycle (4ns), to a list
    of tuples with the format (weight, time_to_integrate_in_ns).
    Can be used to convert between the old format (up to QOP 1.10) to the new format introduced in QOP 1.20.

    :param integration_weights: A list of integration weights.
    :param N:   Maximum number of tuples to return. The algorithm will first create a list of tuples, and then if it is
                too long, it will run :func:`compress_integration_weights` on them.
    :param accuracy:    The accuracy at which to calculate the integration weights. Default is 2^-15, which is
                        the accuracy at which the OPX operates for the integration weights.
    :param plot: If true, plots the integration weights before and after the conversion.
    :type integration_weights: list[float]
    :type N: int
    :type accuracy: float
    :type plot: bool
    :return: List of tuples representing the integration weights
    """
    integration_weights = np.array(integration_weights)
    integration_weights = _round_to_fixed_point_accuracy(integration_weights, accuracy)
    changes_indices = np.where(np.abs(np.diff(integration_weights)) > 0)[0].tolist()
    prev_index = -1
    new_integration_weights = []
    for curr_index in changes_indices + [len(integration_weights) - 1]:
        constant_part = (
            integration_weights[curr_index].tolist(),
            round(4 * (curr_index - prev_index)),
        )
        new_integration_weights.append(constant_part)
        prev_index = curr_index

    new_integration_weights = compress_integration_weights(new_integration_weights, N=N, plot=plot)

    return new_integration_weights


def compress_integration_weights(integration_weights, N=100, plot=False):
    """
    Compresses the list of tuples with the format (weight, time_to_integrate_in_ns) to one with length < N.
    Works by iteratively finding the nearest integration weights and combining them with a weighted average.

    :param integration_weights: The integration_weights to be compressed.
    :param N: The maximum list length required.
    :param plot: If true, plots the integration weights before and after the conversion.
    :return: The compressed list of tuples representing the integration weights.
    """
    integration_weights_before = integration_weights
    integration_weights = np.array(integration_weights)
    while len(integration_weights) > N:
        diffs = np.abs(np.diff(integration_weights, axis=0)[:, 0])
        min_diff = np.min(diffs)
        min_diff_indices = np.where(diffs == min_diff)[0][0]
        times1 = integration_weights[min_diff_indices, 1]
        times2 = integration_weights[min_diff_indices + 1, 1]
        weights1 = integration_weights[min_diff_indices, 0]
        weights2 = integration_weights[min_diff_indices + 1, 0]
        integration_weights[min_diff_indices, 0] = (weights1 * times1 + weights2 * times2) / (times1 + times2)
        integration_weights[min_diff_indices, 1] = times1 + times2
        integration_weights = np.delete(integration_weights, min_diff_indices + 1, 0)
    integration_weights = list(
        zip(
            integration_weights.T[0].tolist(),
            integration_weights.T[1].astype(int).tolist(),
        )
    )
    if plot:
        plt.figure()
        plot_integration_weights(integration_weights_before, label="Original")
        plot_integration_weights(integration_weights, label="Compressed")
        plt.show()
    return integration_weights


def plot_integration_weights(integration_weights, label=None):
    """
    Plot the integration weights in units of ns, receives the integration weights in both formats

    :param integration_weights: The integration_weights to be plotted.
    :param str label: The label of the integration_weights.
    """

    if isinstance(integration_weights[0], tuple):
        a = [[i[0]] * i[1] for i in integration_weights]
        unpacked_weights = sum(a, start=[])
    elif isinstance(integration_weights[0], float):
        a = [[i] * 4 for i in integration_weights]
        unpacked_weights = sum(a, start=[])
    else:
        raise Exception("Unknown input")

    plt.plot(unpacked_weights, label=label)
    if label is not None:
        plt.legend()
