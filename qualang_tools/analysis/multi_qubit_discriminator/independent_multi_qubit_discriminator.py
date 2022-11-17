import numpy as np
import matplotlib.pyplot as plt
import itertools
from tqdm import tqdm
from dataclasses import dataclass

from qualang_tools.analysis.discriminator import two_state_discriminator


def _list_is_rectangular(list):
    for item in list:
        if len(item) != len(list[0]):
            return False

    return True


# switch from igs, iqs, ies, qes to list of [ig, iq, ie, qe], [ig2, iq2, ie2, qe2]
def independent_multi_qubit_discriminator(
    results_list, b_print=True, b_plot=False, text=False
):
    assert _list_is_rectangular(
        results_list
    ), "there is missing data in the results list."

    result_dataclasses = []

    for i, result in enumerate(results_list):
        result_dataclass = _DiscriminatorDataclass(
            f"Qubit_{i}",
            *two_state_discriminator(*result, b_print=b_print, b_plot=b_plot),
            *result,
        )

        result_dataclasses.append(result_dataclass)

    # recursively calculate the overall independent confusion matrix
    A = result_dataclasses[0].confusion_matrix()
    for i in tqdm(range(0, len(result_dataclasses) - 1)):
        B = result_dataclasses[i + 1].confusion_matrix()
        A = np.kron(A, B)

    # rename the variable to make things a little clearer
    outcome = A
    fig, ax = plt.subplots()
    ax.imshow(outcome)

    num_qubits = result_dataclasses.__len__()

    if text:
        state_strings = _generate_labels(num_qubits)
        ticks = np.arange(0, 2**num_qubits)
        ax.set_xticks(ticks)
        ax.set_yticks(ticks)

        ax.set_xticklabels(labels=state_strings)
        ax.set_yticklabels(labels=state_strings)

        ax.set_ylabel("Prepared")
        ax.set_xlabel("Measured")

        ids = list(itertools.product(np.arange(0, outcome.__len__()), repeat=2))

        for id in ids:
            # if on the diagonal id[0] == id[1] and the imshow pixel will be light so make text dark.
            # otherwise pixel will be dark so make text light
            color = "k" if np.all(np.diff(id) == 0) else "w"
            ax.text(
                *id, f"{100 * outcome[id]:.1f}%", ha="center", va="center", color=color
            )

    ax.set_title("Fidelities")
    plt.show()

    return result_dataclasses


def _generate_labels(length):
    out = "{0:b}".format(length)

    strings = list(itertools.product([0, 1], repeat=length))
    out = []

    # if we want to use g/e instead of 0/1
    for string in strings:
        edit_string = "".join(str(x) for x in string)

        edit_string = edit_string.replace("0", "g")
        edit_string = edit_string.replace("1", "e")

        state_string = "|" + edit_string + ">"
        out.append(state_string)

    return out


@dataclass
class _DiscriminatorDataclass:
    """
    Dataclass for holding the results from a two state discriminator run.
    Helper method self.confusion_matrix() generates the confusion matrix from this data.
    """

    name: str

    # parameters
    angle: float
    threshold: float
    fidelity: float
    gg: np.ndarray
    ge: np.ndarray
    eg: np.ndarray
    ee: np.ndarray

    # data
    ig: np.ndarray
    qg: np.ndarray
    ie: np.ndarray
    qe: np.ndarray

    def __post_init__(self):
        """
        adds rotated data to the dataclass
        @return: None
        """
        self.generate_rotation_data()

    def _add_attribute(self, attribute_name, value):
        self.__setattr__(attribute_name, value)

    def confusion_matrix(self):
        """
        Generates and returns the 2x2 state confusion matrix
        @return: 2x2 confusion matrix of state fidelity
        """
        return np.array([[self.gg, self.ge], [self.eg, self.ee]])

    def get_params(self):
        """
        Helper method to quickly obtain useful parameters held in the dataclass
        @return: parameters obtained from the discrimination
        """
        return (
            self.angle,
            self.threshold,
            self.fidelity,
            self.gg,
            self.ge,
            self.eg,
            self.ee,
        )

    def get_data(self):
        """
        Helper method to obtain the data stored in the dataclass
        @return: ground and excited state I/Q data.
        """
        return self.ig, self.qg, self.ie, self.qe

    def get_rotated_data(self):
        """
        Helper method to return the rotated (PCA) data from the measurement.
        @return: ground and excited state I/Q data that has been rotated so maximum information is in I plane.
        """
        return self.ig_rotated, self.qg_rotated, self.ie_rotated, self.qe_rotated

    def generate_rotation_data(self):
        """
        Generates the rotated (PCA) data from the measurement.
        @return: None
        """
        C = np.cos(self.angle)
        S = np.sin(self.angle)

        # Condition for having e > Ig
        if np.mean((self.ig - self.ie) * C - (self.qg - self.qe) * S) > 0:
            self.angle += np.pi
            C = np.cos(self.angle)
            S = np.sin(self.angle)

        self.ig_rotated = self.ig * C - self.qg * S
        self.qg_rotated = self.ig * S + self.qg * C
        self.ie_rotated = self.ie * C - self.qe * S
        self.qe_rotated = self.ie * S + self.qe * C


if __name__ == "__main__":
    iq_state_g = np.random.multivariate_normal(
        (0, -0.2), ((1.5, 0.0), (0.0, 1.5)), (5000, 15)
    ).T
    iq_state_e = np.random.multivariate_normal(
        (-1.8, -3.0), ((1.5, 0), (0, 1.5)), (5000, 15)
    ).T

    Igs, Qgs = iq_state_g
    Ies, Qes = iq_state_e

    results_list = np.stack([Igs, Qgs, Ies, Qes], axis=1)

    results_dataclasses = independent_multi_qubit_discriminator(results_list)
