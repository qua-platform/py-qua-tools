import numpy as np
from matplotlib import pyplot as plt
from scipy.optimize import minimize


def _false_detections(threshold, Ig, Ie):
    if np.mean(Ig) < np.mean(Ie):
        false_detections_var = np.sum(Ig > threshold) + np.sum(Ie < threshold)
    else:
        false_detections_var = np.sum(Ig < threshold) + np.sum(Ie > threshold)
    return false_detections_var


def two_state_discriminator(Ig, Qg, Ie, Qe, b_print=True, b_plot=True):
    """
    Given two blobs in the IQ plane representing two states, finds the optimal threshold to discriminate between them
    and calculates the fidelity. Also returns the angle in which the data needs to be rotated in order to have all the
    information in the `I` (`X`) axis.

    .. note::
        This function assumes that there are only two blobs in the IQ plane representing two states (ground and excited)
        Unexpected output will be returned in other cases.


    :param float Ig: A vector containing the `I` quadrature of data points in the ground state
    :param float Qg: A vector containing the `Q` quadrature of data points in the ground state
    :param float Ie: A vector containing the `I` quadrature of data points in the excited state
    :param float Qe: A vector containing the `Q` quadrature of data points in the excited state
    :param bool b_print: When true (default), prints the results to the console.
    :param bool b_plot: When true (default), plots the results in a new figure.
    :returns: A tuple of (angle, threshold, fidelity, gg, ge, eg, ee).
        angle - The angle (in radians) in which the IQ plane has to be rotated in order to have all the information in
            the `I` axis.
        threshold - The threshold in the rotated `I` axis. The excited state will be when the `I` is larger (>) than
            the threshold.
        fidelity - The fidelity for discriminating the states.
        gg - The matrix element indicating a state prepared in the ground state and measured in the ground state.
        ge - The matrix element indicating a state prepared in the ground state and measured in the excited state.
        eg - The matrix element indicating a state prepared in the excited state and measured in the ground state.
        ee - The matrix element indicating a state prepared in the excited state and measured in the excited state.
    """
    # Condition to have the Q equal for both states:
    angle = np.arctan2(np.mean(Qe) - np.mean(Qg), np.mean(Ig) - np.mean(Ie))
    C = np.cos(angle)
    S = np.sin(angle)
    # Condition for having e > Ig
    if np.mean((Ig - Ie) * C - (Qg - Qe) * S) > 0:
        angle += np.pi
        C = np.cos(angle)
        S = np.sin(angle)

    Ig_rotated = Ig * C - Qg * S
    Qg_rotated = Ig * S + Qg * C

    Ie_rotated = Ie * C - Qe * S
    Qe_rotated = Ie * S + Qe * C

    fit = minimize(
        _false_detections,
        0.5 * (np.mean(Ig_rotated) + np.mean(Ie_rotated)),
        (Ig_rotated, Ie_rotated),
        method="Nelder-Mead",
    )
    threshold = fit.x[0]

    gg = np.sum(Ig_rotated < threshold) / len(Ig_rotated)
    ge = np.sum(Ig_rotated > threshold) / len(Ig_rotated)
    eg = np.sum(Ie_rotated < threshold) / len(Ie_rotated)
    ee = np.sum(Ie_rotated > threshold) / len(Ie_rotated)

    fidelity = 100 * (gg + ee) / 2

    if b_print:
        print(
            f"""
        Fidelity Matrix:
        -----------------
        | {gg:.3f} | {ge:.3f} |
        ----------------
        | {eg:.3f} | {ee:.3f} |
        -----------------
        IQ plane rotated by: {180 / np.pi * angle:.1f}{chr(176)}
        Threshold: {threshold:.3e}
        Fidelity: {fidelity:.1f}%
        """
        )

    if b_plot:
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2)
        ax1.plot(Ig, Qg, ".", alpha=0.1, label="Ground", markersize=2)
        ax1.plot(Ie, Qe, ".", alpha=0.1, label="Excited", markersize=2)
        ax1.axis("equal")
        ax1.legend(["Ground", "Excited"])
        ax1.set_xlabel("I")
        ax1.set_ylabel("Q")
        ax1.set_title("Original Data")

        ax2.plot(Ig_rotated, Qg_rotated, ".", alpha=0.1, label="Ground", markersize=2)
        ax2.plot(Ie_rotated, Qe_rotated, ".", alpha=0.1, label="Excited", markersize=2)
        ax2.axis("equal")
        ax2.set_xlabel("I")
        ax2.set_ylabel("Q")
        ax2.set_title("Rotated Data")

        ax3.hist(Ig_rotated, bins=50, alpha=0.75, label="Ground")
        ax3.hist(Ie_rotated, bins=50, alpha=0.75, label="Excited")
        ax3.axvline(x=threshold, color="k", ls="--", alpha=0.5)
        text_props = dict(
            horizontalalignment="center",
            verticalalignment="center",
            transform=ax3.transAxes,
        )
        ax3.text(0.7, 0.9, f"{threshold:.3e}", text_props)
        ax3.set_xlabel("I")
        ax3.set_title("1D Histogram")

        ax4.imshow(np.array([[gg, ge], [eg, ee]]))
        ax4.set_xticks([0, 1])
        ax4.set_yticks([0, 1])
        ax4.set_xticklabels(labels=["|g>", "|e>"])
        ax4.set_yticklabels(labels=["|g>", "|e>"])
        ax4.set_ylabel("Prepared")
        ax4.set_xlabel("Measured")
        ax4.text(0, 0, f"{100 * gg:.1f}%", ha="center", va="center", color="k")
        ax4.text(1, 0, f"{100 * ge:.1f}%", ha="center", va="center", color="w")
        ax4.text(0, 1, f"{100 * eg:.1f}%", ha="center", va="center", color="w")
        ax4.text(1, 1, f"{100 * ee:.1f}%", ha="center", va="center", color="k")
        ax4.set_title("Fidelities")
        fig.tight_layout()

    return angle, threshold, fidelity, gg, ge, eg, ee
