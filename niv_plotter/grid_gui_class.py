"""
A GUI for presenting state discrimination data for a multi-qubit setup.
"""

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
from multiprocessing import Process


class PlotWidget(pg.GraphicsWidget):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def mouseDoubleClickEvent(self, QGraphicsSceneMouseEvent):
        print('test')

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
        self.setup_plot_layouts()
        # self.set_plot_data()

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

        plot = self.get_layout(index)

        plot.clear()
        plot.plot(*data)

        plot.showAxis('bottom')
        plot.showAxis('left')
        plot.showButtons()

    def set_plot_to_text(self, index, text):
        plot = self.get_layout(index)

        plot.addItem(pg.TextItem('99.9'))
        #
        # plot.clear()
        #
        # plot.addItem(PlotWidget())

    def set_plot_custom(self, index):
        box = self.plot_layout.getViewBox(index)

        return box

    def update_plot_title(self, index, new_title):

        plot = self.get_layout(index)
        plot.setTitle(new_title)

    def set_text(self, index, text):
        self.plot_layout.removeItem(self.plot_layout.getItem(*index))
        self.plot_layout.addLabel(text, *index)

    def get_layout(self, index):
        i, j = index
        return self.plot_layouts[i][j]

    def setup_plot_layouts(self):

        self.plot_layouts = []

        for i in range(self.x):
            row = []
            for j in range(self.y):
                # plot = self.plot_layout.addPlot(title=f'qubit [{i}{j}]')
                plot = self.plot_layout.addLayout(rowspan=1, colspan=1)
                row.append(plot)
                # plot.hideAxis('bottom')
                # plot.hideAxis('left')
                # plot.hideButtons()
            self.plot_layouts.append(row)
            self.plot_layout.nextRow()

    def set_plot_data(self):
        for index, data in self.data.items():
            self.update_plot(index, data)

    def mouse_clicked(self, event):
        # print(f'{event}')

        pass

    def get_plots(self):
        return self.plot_layouts

