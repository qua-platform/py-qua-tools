import numpy as np
from gui import GUI


def fake_function(x):
    x0 = (np.random.rand()) * 0.8
    return 1 - (1 / (1 + ((x - x0) / 0.25) ** 2))


def fake_data():
    x = np.linspace(0, 1, 100)
    y = fake_function(x)
    y += np.random.rand(y.size) * 0.2
    return x * 1e6, y + 3 * np.random.rand()


# set up qubit grid shape
i = 2
j = 2
grid_size = (i, j)

# launch the gui
gui = GUI(grid_size, ipython=True)

# the address for each gui element is a tuple (i, j)
qubits = ((0, 0), (0, 1), (1, 0), (1, 1))
x = np.linspace(-1, 2, 100)
y = np.linspace(-1, 3, 100)

random_data = lambda: np.fromfunction(
    lambda i, j: np.sin(i / 8 * np.random.rand()) * j / 128, (100, 100), dtype=float
) + np.random.rand(100, 100)


# you have three options: 0d (text), 1d, and 2d.
# for 0d, just have the data item (text or digit)
# for 1d, you need to provide x and y data, both 1d array-like objects
# for 2d, you need to provide x and y data (1d array-like), and your 2d array-like data array

# the way to do it is to call gui.plot_xd(qubit_address (e.g. (0, 0), layer name, x, y....)

for qubit in qubits:
    gui.plot_0d(qubit, "Fidelity", f"{np.random.rand() * 100:.2f}%")
    gui.plot_1d(qubit, "spect", *fake_data())
    gui.plot_2d(qubit, "osc", x, y, random_data())


# if you like, you can update the data in a layer by gui.update_layer(qubit_address (i, j), layer_name, data)
