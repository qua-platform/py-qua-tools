"""
A GUI for presenting state discrimination data for a multi-qubit setup.
"""


from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np
import time

from .widget import StackedWidget


class GUI(QWidget):
    def __init__(self, grid_size, ipython=True):
        self.app = pg.mkQApp()

        super(GUI, self).__init__()

        self.grid_size = grid_size

        self.initialise_ui()
        # self.setup_controls()
        self.setup_qubit_plot_grid()

        if ipython:
            from IPython import get_ipython

            ipy = get_ipython()
            ipy.run_line_magic("gui", "qt5")

        else:
            pg.exec()

    def initialise_ui(self):
        self.main_window = QMainWindow()
        self.main_window.resize(1000, 800)
        self.setAutoFillBackground(True)

        self.main_window.setCentralWidget(self)
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)

        self.main_window.setWindowTitle("Quantum Machines qubit viewer")

        self.main_window.show()

    def setup_controls(self):

        self.control_layout = QHBoxLayout()
        self.main_layout.addLayout(self.control_layout)

        self.reset_views_button = QPushButton("Reset views")
        self.control_layout.addWidget(self.reset_views_button)
        self.reset_views_button.clicked.connect(self._reset_views)

        self.set_to_fidelity_button = QPushButton("Show fidelities")
        self.set_to_data_button = QPushButton("Show data")
        self.control_layout.addWidget(self.set_to_fidelity_button)
        self.control_layout.addWidget(self.set_to_data_button)

        self.set_to_data_button.clicked.connect(self._set_all_to_data)
        self.set_to_fidelity_button.clicked.connect(self._set_all_to_fidelity)

    def _set_all_to_data(self):
        for row in self.widgets:
            for widget in row:
                # if widget.view_widget.hidden and hasattr(widget.view_widget, 'plot_item'):
                #     widget.view_widget.toggle_hide()
                widget.Stack.setCurrentIndex(0)

    def _set_all_to_fidelity(self):
        for row in self.widgets:
            for widget in row:
                # if not widget.view_widget.hidden and hasattr(widget.view_widget, 'plot_item'):
                #     widget.view_widget.toggle_hide()
                widget.Stack.setCurrentIndex(1)

    def _reset_views(self):
        for row in self.widgets:
            for widget in row:
                widget.Stack.currentWidget().autoRange()

    def setup_qubit_plot_grid(self):
        self.plot_grid_layout = QGridLayout()
        self.main_layout.addLayout(self.plot_grid_layout)

        self.widgets = []

        for i in range(self.grid_size[0]):
            row = []
            self.plot_grid_layout.setRowStretch(i, 1)
            for j in range(self.grid_size[1]):
                self.plot_grid_layout.setColumnStretch(j, 1)
                widget = StackedWidget(f"qubit [{i}{j}]")
                self.plot_grid_layout.addWidget(widget, i, j)
                row.append(widget)
            self.widgets.append(row)

    def get_widget(self, index):
        return self.widgets[index[0]][index[1]]

    def update_layer(self, index, layer_name, x, y=None, z=None):
        widget = self.get_widget(index)
        widget.update_layer_data(layer_name, x, y, z)

    def plot_1d(self, index, name, x, y):
        widget = self.get_widget(index)
        widget.add_1d_plot(name, x, y)

    def plot_2d(self, index, name, x, y, z):
        widget = self.get_widget(index)
        widget.add_2d_plot(name, x, y, z)

    def plot_0d(self, index, name, value):
        widget = self.get_widget(index)
        widget.add_0d_plot(name, value)
