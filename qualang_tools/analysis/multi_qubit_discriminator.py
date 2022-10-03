import numpy as np
import matplotlib.pyplot as plt
import itertools

from discriminator import two_state_discriminator

def multi_qubit_discriminator(Igs, Qgs, Ies, Qes):


    assert len(Igs) == len(Qgs) == len(Ies) == len(Qes), "we don't have full readout for all qubits"


    ggs, ges, egs, ees = [], [], [], []

    confusion_matrices = []


    for Ig, Qg, Ie, Qe in zip(Igs, Qgs, Ies, Qes):

        angle, threshold, fidelity, gg, ge, eg, ee = two_state_discriminator(Ig, Qg, Ie, Qe, b_print=True)
        ggs.append(gg)
        ges.append(ge)
        egs.append(eg)
        ees.append(ee)

        confusion_matrices.append(np.array([
            [gg, ge],
            [eg, ee]
        ]))



    return ggs, ges, egs, ees, confusion_matrices

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

    iq_state_g = np.random.multivariate_normal((0, -0.2), ((1.5, 0.), (0., 1.5)), (5000, 4)).T
    iq_state_e = np.random.multivariate_normal((-1.8, -3.), ((1.5, 0), (0, 1.5)), (5000, 4)).T

    igs, qgs = iq_state_g
    ies, qes = iq_state_e

    ggs, ges, egs, ees, confusion_matrices = multi_qubit_discriminator(igs, qgs, ies, qes)

    # need to fix this so it's [ab], c etc [[ab] c][d]

    A = confusion_matrices[0]

    for i in range(0, len(confusion_matrices) - 1):

        B = confusion_matrices[i + 1]

        A = np.kron(A, B)

    outcome = A
    fig, ax = plt.subplots()
    ax.imshow(outcome)

    num_qubits = igs.__len__()

    state_strings = generate_labels(num_qubits)

    ticks = np.arange(0, outcome.__len__())
    ax.set_xticks(ticks)
    ax.set_yticks(ticks)

    ax.set_xticklabels(labels=state_strings)
    ax.set_yticklabels(labels=state_strings)

    ax.set_ylabel("Prepared")
    ax.set_xlabel("Measured")

    ids = list(itertools.product(np.arange(0, outcome.__len__()), repeat=2))
    print(ids)
    for id in ids:

        # if on the diagonal id[0] == id[1] and the imshow pixel will be light so make text dark.
        # otherwise pixel will be dark so make text light
        color = 'k' if np.all(np.diff(id) == 0) else 'w'

        print(id)

        ax.text(*id, f"{100 * outcome[id]:.1f}%", ha="center", va="center", color=color)

    #
    # ax.text(0, 0, f"{100 * gg:.1f}%", ha="center", va="center", color="k")
    # ax.text(1, 0, f"{100 * ge:.1f}%", ha="center", va="center", color="w")
    # ax.text(0, 1, f"{100 * eg:.1f}%", ha="center", va="center", color="w")
    # ax.text(1, 1, f"{100 * ee:.1f}%", ha="center", va="center", color="k")
    ax.set_title("Fidelities")

    plt.show()
