"""
A GUI for presenting state discrimination data for a multi-qubit setup.
"""

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
from multiprocessing import Process


class MyPlotWidget(pg.PlotWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # self.scene() is a pyqtgraph.GraphicsScene.GraphicsScene.GraphicsScene
        self.scene().sigMouseClicked.connect(self.mouse_clicked)

    def mouse_clicked(self, mouseClickEvent):
        # mouseClickEvent is a pyqtgraph.GraphicsScene.mouseEvents.MouseClickEvent
        print('clicked plot 0x{:x}, event: {}'.format(id(self), mouseClickEvent))


class GUI(QWidget):
    def __init__(self, array_shape, data_dict, ipython=False):
        """
        GUI for presenting per-qubit readout information as well as a general overview dashboard which
        contains some information. More to be added later.

        @param results_dataclasses: results dataclass
        """

        self.app = pg.mkQApp()

        # self.qubit_array_shape = (8, 8)
        self.qubit_array_shape = array_shape
        self.x, self.y = self.qubit_array_shape

        # self.qubits = ((0, 0), (0, 1), (1, 1), (2, 2), (2, 3), (3, 3), (3, 4), (4, 4))
        self.data = data_dict
        self.qubits = tuple(data_dict.keys())
        super(GUI, self).__init__()

        self.initialise_ui()
        self.setup_plot_items()
        self.set_plot_data()

        # self.setup_plots()

        if not ipython:
            pg.exec()

        if ipython:
            from IPython import get_ipython
            ipy = get_ipython()
            ipy.run_line_magic('gui', 'qt5')

    def initialise_ui(self):
        self.view = pg.GraphicsView()
        self.plot_layout = pg.GraphicsLayout(border=(100, 100, 100))
        self.view.setCentralItem(self.plot_layout)
        self.view.show()
        self.view.setWindowTitle("Quantum Machines qubit viewer")
        self.view.resize(800, 600)

    def update_plot(self, index, data):

        plot = self.get_plot(index)

        plot.clear()
        plot.plot(*data)

        plot.showAxis('bottom')
        plot.showAxis('left')
        plot.showButtons()

    def set_plot_to_text(self, index, text):
        plot = self.get_plot(index)
        plot.clear()


    def update_plot_title(self, index, new_title):

        plot = self.get_plot(index)
        plot.setTitle(new_title)

    def set_text(self, index, text):
        self.plot_layout.removeItem(self.plot_layout.getItem(*index))
        self.plot_layout.addLabel(text, *index)

    def get_plot(self, index):
        i, j = index
        return self.plots[i][j]

    def setup_plot_items(self):

        self.plots = []

        for i in range(self.x):
            row = []
            for j in range(self.y):
                plot = self.plot_layout.addPlot(title=f'qubit [{i}{j}]')
                row.append(plot)
                plot.hideAxis('bottom')
                plot.hideAxis('left')
                plot.hideButtons()
            self.plots.append(row)
            self.plot_layout.nextRow()

    def set_plot_data(self):
        for index, data in self.data.items():
            self.update_plot(index, data)

    def setup_plots(self):
        self.plots = []
        for i in range(self.x):
            row = []
            for j in range(self.y):
                plot = self.plot_layout.addPlot(title=f'Qubit[{i}{j}]')
                row.append(plot)

                if (i, j) in self.qubits:
                    plot.plot(*self.data[(i, j)])
                else:
                    plot.hideAxis('bottom')
                    plot.hideAxis('left')
                    plot.hideButtons()

                plot.scene().sigMouseClicked.connect(self.mouse_clicked)

            self.plots.append(row)
            self.plot_layout.nextRow()

    def mouse_clicked(self, event):
        # print(f'{event}')

        pass

    def fake_function(self, x):
        x0 = (0.5 - np.random.rand()) * 0.8
        return 1 - (1 / (1 + ((x - x0) / 0.25) ** 2))

    def fake_data(self):
        x = np.linspace(-1, 1, 100)
        y = self.fake_function(x)
        y += np.random.rand(y.size) * 0.2
        return x, y

    def get_plots(self):
        return self.plots


def launch_discriminator_gui():
    # app = pg.mkQApp()
    loader = GUI()
    pg.exec()
    return loader


# example with fake data
if __name__ == "__main__":
    # proc = Process(target=launch_discriminator_gui, daemon=True)
    x = launch_discriminator_gui()
    # proc.start()/
