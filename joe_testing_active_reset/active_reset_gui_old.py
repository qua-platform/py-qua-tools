# from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QListWidget, QLineEdit, QTabWidget, QGridLayout, \
#     QVBoxLayout

from PyQt5.QtWidgets import *

import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QT_LIB, QtCore, QtGui, QtWidgets

from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget


# just use widget doesn't need an app window
class ActiveReset(QApplication):

    # def __init__(self, num_qubits):
    #     super().__init__([])
    #     self.num_qubits = num_qubits
    #
    #     self.main_window = QWidget()
    #     self.main_window.setWindowTitle('Active reset viewer')
    #
    #     self.splitter = QSplitter()
    #     self.splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
    #     self.layout_widget = QtWidgets.QWidget(self.splitter)
    #
    #
    #     # create some widgets
    #     self.qubit_list = QListWidget()
    #
    #     self.graphics_window = pg.GraphicsLayoutWidget()
    #     self.plt1 = self.graphics_window.addPlot()
    #     self.plt2 = self.graphics_window.addPlot()
    #
    #
    #     # self.graphics_window.ci.setBorder((50, 50, 100))
    #
    #     # self.passive_reset_layout = self.graphics_window.addLayout()
    #     # self.passive_reset_layout.addLabel("<b>Passive reset</b>")
    #     # self.passive_reset_layout.nextRow()
    #     # self.passive_view_box = self.passive_reset_layout.addViewBox()
    #     #
    #     # self.active_reset_layout = self.graphics_window.addLayout()
    #     # self.active_reset_layout.addLabel("<b>Active reset</b>")
    #     # self.active_reset_layout.nextRow()
    #
    #     # self.active_view_box = self.active_reset_layout.addViewBox()
    #     self.text = QWidget()
    #     self.text_layout = QGridLayout()
    #     self.text.setLayout(self.text_layout)
    #     self.set_up_text_area()
    #
    #     self.main_layout = QGridLayout()
    #
    #     self.main_window.setLayout(self.main_layout)
    #
    #
    #     self.main_layout.addWidget(self.qubit_list, 0, 0, 2, 1)
    #     self.main_layout.addWidget(self.text, 2, 0, 2, 1)
    #     # self.main_layout.addWidget(self.splitter, 0, 2, 1, 1)
    #     self.main_layout.addWidget(self.graphics_window, 0, 3, 4, 6)
    #
    #     self.populate_list()
    #     self.qubit_list.itemDoubleClicked.connect(self.func)
    #
    #
    #     self.main_window.show()

    def __init__(self, num_qubits):
        super().__init__([])
        self.num_qubits = num_qubits

        self.main_window = QWidget()
        self.main_window.setWindowTitle('Active reset viewer')
        

        self.splitter = QSplitter()



        # create some widgets
        self.qubit_list = QListWidget()

        self.graphics_window = pg.GraphicsLayoutWidget()
        self.plt1 = self.graphics_window.addPlot()
        self.plt2 = self.graphics_window.addPlot()

        self.text = QWidget()
        self.text_layout = QGridLayout()
        self.text.setLayout(self.text_layout)
        self.set_up_text_area()


        self.graphics_window.ci.setBorder((50, 50, 100))

        self.passive_reset_layout = self.graphics_window.addLayout()
        self.passive_reset_layout.addLabel("<b>Passive reset</b>")
        self.passive_reset_layout.nextRow()
        self.passive_view_box = self.passive_reset_layout.addViewBox()

        self.active_reset_layout = self.graphics_window.addLayout()
        self.active_reset_layout.addLabel("<b>Active reset</b>")
        self.active_reset_layout.nextRow()

        self.active_view_box = self.active_reset_layout.addViewBox()


        self.main_layout = QGridLayout()

        self.main_window.setLayout(self.main_layout)


        self.main_layout.addWidget(self.qubit_list, 0, 0, 2, 1)
        self.main_layout.addWidget(self.text, 2, 0, 2, 1)
        # self.main_layout.addWidget(self.splitter, 0, 2, 1, 1)
        self.main_layout.addWidget(self.graphics_window, 0, 3, 4, 6)

        self.populate_list()
        self.qubit_list.itemDoubleClicked.connect(self.func)


        self.main_window.show()

    def set_up_text_area(self):

        self.info_title = QLabel('<b>Fidelity information for qubit ')
        self.info_passive_title = QLabel('<b>Passive</b>')
        self.info_active_title = QLabel('<b>Active</b>')

        self.info_passive_fid = QLabel('Fidelity: ')
        self.info_passive_time = QLabel('Time: ')

        self.info_active_fid = QLabel('Fidelity: ')
        self.info_active_time = QLabel('Time: ')

        self.text_layout.addWidget(self.info_title, 0, 0, 1, 1)
        self.text_layout.addWidget(self.info_passive_title, 1, 0)
        self.text_layout.addWidget(self.info_active_title, 1, 1)

        self.text_layout.addWidget(self.info_passive_fid, 2, 0)
        self.text_layout.addWidget(self.info_passive_time, 3, 0)
        self.text_layout.addWidget(self.info_active_fid, 2, 1)
        self.text_layout.addWidget(self.info_active_time, 3, 1)


    def update_text_area(self, qubit_id):

        self.info_title.setText(f'<b>Fidelity information for qubit {qubit_id}')

        self.info_passive_fid.setText(f'Fidelity: {100 * (1 - (0.2 * np.random.rand())):.1f}%')
        self.info_passive_time.setText(f'Time: {98.5} ns')
        self.info_active_fid.setText(f'Fidelity: {100 * (1 - (0.2 * np.random.rand())):.1f}%')
        self.info_active_time.setText(f'Time: {100} ns')

    def func(self):

        self.plt1.clear()
        self.plt2.clear()

        y, x, y2, x2 = self.generate_fake_histograms(1, 1)

        ## Using stepMode="center" causes the plot to draw two lines for each sample.
        ## notice that len(x) == len(y)+1
        self.plt1.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        self.plt1.plot(x2, y2, stepMode="center", fillLevel=0, fillOutline=True, brush=(255, 69, 0, 150))

        y, x, y2, x2 = self.generate_fake_histograms(0.2, 1.8)
        self.plt2.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        self.plt2.plot(x2, y2, stepMode="center", fillLevel=0, fillOutline=True, brush=(255, 69, 0, 150))

    """
    def func(self):

        qubit = self.qubit_list.currentRow()

        # clear the view boxes so we don't plot histograms on top of each other
        self.passive_view_box.clear()
        self.active_view_box.clear()
        y, x, y2, x2 = self.generate_fake_histograms(1, 1)
        figure1 = pg.PlotDataItem(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        figure2 = pg.PlotDataItem(x2, y2, stepMode="center", fillLevel=0, fillOutline=True, brush=(255, 69, 0, 150))
        self.passive_view_box.addItem(figure1)
        self.passive_view_box.addItem(figure2)

        y, x, y2, x2 = self.generate_fake_histograms(0.2, 1.8)
        figure3 = pg.PlotDataItem(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(0, 0, 255, 150))
        figure4 = pg.PlotDataItem(x2, y2, stepMode="center", fillLevel=0, fillOutline=True, brush=(255, 69, 0, 150))

        self.active_view_box.addItem(figure3)
        self.active_view_box.addItem(figure4)

        self.update_text_area(qubit + 1)
        
    """


    def generate_fake_histograms(self, a, b):
        ## make interesting distribution of values
        vals1 = np.random.normal(size=500)
        vals2 = np.random.normal(size=260, loc=4)
        ## compute standard histogram
        y, x = np.histogram(vals1, bins=np.linspace(-3, 8, 80))
        y2, x2 = np.histogram(vals2, bins=np.linspace(-3, 8, 80))
        return a * y, x, b * y2, x2

    def populate_list(self):

        for i in range(self.num_qubits):
            self.qubit_list.addItem(
                f'Qubit {i + 1}'
            )




if __name__ == '__main__':
    app = ActiveReset(32)
    app.exec_()
