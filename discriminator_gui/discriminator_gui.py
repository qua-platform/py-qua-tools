import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np

class DiscriminatorGui(QWidget):
    def __init__(self, results_dataclasses):

        self.num_qubits = len(results_dataclasses)
        self.results_dataclasses = results_dataclasses
        super(DiscriminatorGui, self).__init__()
        self.initUI()
        self._populate_list()


    def initUI(self):

        hbox = QHBoxLayout(self)

        # create some widgets

        self.left = pg.LayoutWidget()
        self.right = pg.LayoutWidget()

        self.qubit_list = QComboBox()


        self.graphics_window = pg.GraphicsLayoutWidget()
        self.plt1 = self.graphics_window.addPlot(title='<font size="+1"><b>Original data</b></font>')
        self.plt2 = self.graphics_window.addPlot(title='<font size="+1"><b>Rotated data</b></font>')
        self.graphics_window.nextRow()
        self.plt3 = self.graphics_window.addPlot(title='<font size="+1"><b>1D Histogram</b></font>')
        self.plt4 = self.graphics_window.addPlot(title='<font size="+1"><b>Fidelities</b></font>')

        self.left.addWidget(self.qubit_list, 0, 0)
        self.left.addWidget(QFrame(), 2, 0)

        self.right.addWidget(self.graphics_window)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)


        hbox.addWidget(splitter)

        self.setLayout(hbox)

        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))

        self.setGeometry(100, 100, 1200, 500)
        self.setWindowTitle('Qubit reset comparison')

        # self.qubit_list.itemDoubleClicked.connect(self.func)
        self.qubit_list.currentIndexChanged.connect(self.func)


        self.show()

    def generate_fake_histograms(self, a, b):
        ## make interesting distribution of values
        vals1 = np.random.normal(size=500)
        vals2 = np.random.normal(size=260, loc=4)
        ## compute standard histogram
        y, x = np.histogram(vals1, bins=np.linspace(-3, 8, 80))
        y2, x2 = np.histogram(vals2, bins=np.linspace(-3, 8, 80))
        return a * y, x, b * y2, x2

    def clear_plots(self):
        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt4.clear()

    def func(self):

        self.clear_plots()

        index = self.qubit_list.currentIndex()
        result = self.results_dataclasses[index]

        angle, threshold, fidelity, gg, ge, eg, ee = result.get_params()
        ig, qg, ie, qe = result.get_data()
        ig_rotated, qg_rotated, ie_rotated, qe_rotated = result.get_rotated_data()

        ## Using stepMode="center" causes the plot to draw two lines for each sample.
        ## notice that len(x) == len(y)+1

        original_data_g = pg.ScatterPlotItem(ig, qg, brush=(50, 50, 50, 199))
        original_data_e = pg.ScatterPlotItem(ie, qe, brush=(0, 0, 100, 100))
        self.plt1.addItem(original_data_g)
        self.plt1.addItem(original_data_e)


        rotated_data_g = pg.ScatterPlotItem(ig_rotated, qg_rotated, brush=(50, 50, 50, 199))
        rotated_data_e = pg.ScatterPlotItem(ie_rotated, qe_rotated, brush=(0, 0, 100, 100))
        self.plt2.addItem(rotated_data_g)
        self.plt2.addItem(rotated_data_e)

        ig_hist_y, ig_hist_x = np.histogram(ig_rotated, bins=50)
        ie_hist_y, ie_hist_x = np.histogram(ie_rotated, bins=50)

        self.plt3.plot(ig_hist_x, ig_hist_y, stepMode="center", fillLevel=0, fillOutline=False, brush=(0, 0, 0, 255))
        self.plt3.plot(ie_hist_x, ie_hist_y, stepMode="center", fillLevel=0, fillOutline=False, brush=(255, 255, 255, 150))

        img = pg.ImageItem(image=result.confusion_matrix())
        self.plt4.addItem(img)
        self.plt4.showAxes(False)



    def _populate_list(self):

        for i in range(self.num_qubits):
            self.qubit_list.addItem(
                f'Qubit {i + 1}'
            )





if __name__ == '__main__':

    from qualang_tools.analysis.independent_multi_qubit_discriminator import independent_multi_qubit_discriminator

    iq_state_g = np.random.multivariate_normal((0, -0.2), ((1.5, 0.), (0., 1.5)), (5000, 32)).T
    iq_state_e = np.random.multivariate_normal((-1.8, -3.), ((1.5, 0), (0, 1.5)), (5000, 32)).T

    igs, qgs = iq_state_g
    ies, qes = iq_state_e

    results = independent_multi_qubit_discriminator(igs, qgs, ies, qes, b_plot=False, b_print=False)

    def main():
        app = pg.mkQApp()
        # loader = multiQubitReadoutPresenter(results)
        loader = DiscriminatorGui(results)
        pg.exec()

    main()
