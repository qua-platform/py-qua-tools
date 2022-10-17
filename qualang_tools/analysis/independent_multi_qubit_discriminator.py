import numpy as np
import matplotlib.pyplot as plt
import itertools
from tqdm import tqdm

from .discriminator import two_state_discriminator
from .results_dataclass import DiscriminatorDataclass


def independent_multi_qubit_discriminator(Igs, Qgs, Ies, Qes, b_print=True, b_plot=True, text=False):
    assert len(Igs) == len(Qgs) == len(Ies) == len(Qes), "we don't have full readout information for all qubits"

    result_dataclasses = []

    for i, (Ig, Qg, Ie, Qe) in enumerate(zip(Igs, Qgs, Ies, Qes)):
        result_dataclass = DiscriminatorDataclass(
            f'Qubit_{i}',
            *two_state_discriminator(
                Ig, Qg, Ie, Qe, b_print=b_print, b_plot=b_plot),
            Ig, Qg, Ie, Qe
        )

        result_dataclasses.append(result_dataclass)

    # recursively calculate the overall independent confusion matrix
    A = result_dataclasses[0].confusion_matrix()
    # for i in tqdm(range(0, len(result_dataclasses) - 1)):
    #     B = result_dataclasses[i + 1].confusion_matrix()
    #     A = np.kron(A, B)

    # rename the variable to make things a little clearer
    outcome = A
    fig, ax = plt.subplots()
    ax.imshow(outcome)

    num_qubits = result_dataclasses.__len__()

    if text:
        state_strings = generate_labels(num_qubits)
        ticks = np.arange(0, 2 ** num_qubits)
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
            color = 'k' if np.all(np.diff(id) == 0) else 'w'
            ax.text(*id, f"{100 * outcome[id]:.1f}%", ha="center", va="center", color=color)

    ax.set_title("Fidelities")
    plt.show()

    return result_dataclasses


def generate_labels(length):
    out = '{0:b}'.format(length)

    strings = list(itertools.product([0, 1], repeat=length))
    out = []

    # if we want to use g/e instead of 0/1
    for string in strings:
        edit_string = ''.join(str(x) for x in string)

        edit_string = edit_string.replace('0', 'g')
        edit_string = edit_string.replace('1', 'e')

        state_string = '|' + edit_string + '>'
        out.append(state_string)

    return out


if __name__ == '__main__':
    iq_state_g = np.random.multivariate_normal((0, -0.2), ((1.5, 0.), (0., 1.5)), (5000, 15)).T
    iq_state_e = np.random.multivariate_normal((-1.8, -3.), ((1.5, 0), (0, 1.5)), (5000, 15)).T

    Igs, Qgs = iq_state_g
    Ies, Qes = iq_state_e

    independent_multi_qubit_discriminator(Igs, Qgs, Ies, Qes)
