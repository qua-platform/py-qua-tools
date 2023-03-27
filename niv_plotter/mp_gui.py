import pyqtgraph as pg
import numpy as np


pg.mkQApp()


def fake_function(x):
    x0 = (0.5 - np.random.rand()) * 0.8
    return 1 - (1 / (1 + ((x - x0) / 0.25) ** 2))


def fake_data():
    x = np.linspace(-1, 1, 100)
    y = fake_function(x)
    y += np.random.rand(y.size) * 0.2
    return x, y

x = 5
y = 5
qubits = ((1, 1), (2, 2))


# Create remote process with a plot window
import pyqtgraph.multiprocess as mp
proc = mp.QtProcess()
rpg = proc._import('pyqtgraph')

view = rpg.GraphicsView()
l = rpg.GraphicsLayout(border=(100, 100, 100))
view.setCentralItem(l)
view.show()

plots = []

for i in range(x):
    row = []
    for j in range(y):
        plot = l.addPlot(title=f'Qubit[{i}{j}]')
        row.append(plot)

        if (i, j) in qubits:
            plot.plot(*fake_data())
        else:
            plot.hideAxis('bottom')
            plot.hideAxis('left')
            plot.hideButtons()

    plots.append(row)
    l.nextRow()

