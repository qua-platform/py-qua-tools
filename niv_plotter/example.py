from grid_gui_class import GUI
import numpy as np

def fake_function(x):
    x0 = (0.5 - np.random.rand()) * 0.8
    return 1 - (1 / (1 + ((x - x0) / 0.25) ** 2))


def fake_data():
    x = np.linspace(-1, 1, 100)
    y = fake_function(x)
    y += np.random.rand(y.size) * 0.2
    return x, y


# run something
qubit_arrangement = (4, 5)
qubits = ((0, 0), (1, 1), (2, 2), (2, 3), (3, 2), (3, 3), (3, 4))
data = {qubit: fake_data() for qubit in qubits}



gui = GUI(qubit_arrangement, data, ipython=True)
