# File to show for example how the reset comparison gui could work

import numpy as np
from qualang_tools.plot import ActiveResetGUI
from PyQt5.QtWidgets import QApplication
import sys



def generate_discrimination_data():
    from qualang_tools.analysis.multi_qubit_discriminator.independent_multi_qubit_discriminator import independent_multi_qubit_discriminator

    iq_state_g = np.random.multivariate_normal((0, -0.2), ((1.5, 0.), (0., 1.5)), (5000, 10)).T
    iq_state_e = np.random.multivariate_normal((-1.8, -3.), ((1.5, 0), (0, 1.5)), (5000, 10)).T

    igs, qgs = iq_state_g
    ies, qes = iq_state_e

    results_list = np.stack([igs, qgs, ies, qes], axis=1)


    results = independent_multi_qubit_discriminator(results_list, b_plot=False, b_print=False)
    [result._add_attribute('runtime', 100 * np.random.rand()) for result in results]
    return results


# output would be a dictionary like this:
reset_dict = {
    'Passive reset': generate_discrimination_data(),
    'Active reset': generate_discrimination_data(),
    'New method': generate_discrimination_data(),
    'Other method': generate_discrimination_data()
}

def main():
    app = QApplication(sys.argv)
    ex = ActiveResetGUI(reset_dict)
    # sys.exit(app.exec_())
    app.exec_()

if __name__ == '__main__':
    main()