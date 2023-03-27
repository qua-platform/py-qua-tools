"""
Demonstrate the use of layouts to control placement of multiple plots / views /
labels
"""

import numpy as np
import pyqtgraph as pg
import threading
from multiprocessing import Process


def fake_function(x):
    x0 = (0.5 - np.random.rand()) * 0.8
    return (1 / (1 + ((x - x0) / 0.25)**2))

def fake_data():
    x = np.linspace(-1, 1, 100)
    y = fake_function(x)
    y += np.random.rand(y.size) * 0.2
    return x, y

def click_function():
    print('something has been clicked')


qubit_array_shape = (5, 5)

qubits = ((0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4))

x, y = qubit_array_shape

app = pg.mkQApp("Gradiant Layout Example")
view = pg.GraphicsView()
l = pg.GraphicsLayout(border=(100,100,100))
view.setCentralItem(l)
view.show()
view.setWindowTitle("Niv's special viewer")
view.resize(800,600)



plots = []
for i in range(x):
    row = []
    for j in range(y):
        plot = l.addPlot(title=f'Qubit[{i}{j}]')
        row.append(plot)
    plots.append(row)
    l.nextRow()

for i, row in enumerate(plots):
    for j, plot in enumerate(row):
        if (i, j) in qubits:
            plot.plot(*fake_data())
        else:
            plot.hideAxis('bottom')
            plot.hideAxis('left')
            plot.hideButtons()




def launch_program():
    app = pg.mkQApp()
    pg.exec()

if __name__ == '__main__':
    from PyQt5.QtCore import *
    from PyQt5.QtWidgets import *
    import sys
    x = Process(target=launch_program(), daemon=True)
    x.start()
    x.join()
