import sys
from PyQt5.QtCore import *
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np

# TODO: create brushes to use throughout for ground/excited states
# TODO: sort out the axes so plot 4 has the axes around the image rather than the plot area
# TODO: add tab with additional info from Niv

class DiscriminatorGui(QWidget):
    def __init__(self, results_dataclasses):

        self.num_qubits = len(results_dataclasses)
        self.results_dataclasses = results_dataclasses
        super(DiscriminatorGui, self).__init__()
        self.initialise_ui()
        self._populate_list()


    def initialise_ui(self):

        box_layout = QHBoxLayout(self)

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


        box_layout.addWidget(splitter)

        self.setLayout(box_layout)

        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))

        self.setGeometry(100, 100, 1100, 700)
        self.setWindowTitle('Readout viewer')

        # self.qubit_list.itemDoubleClicked.connect(self.func)
        self.qubit_list.currentIndexChanged.connect(self.func)


        self.show()


    def clear_plots(self):
        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt4.clear()

    def _generate_plot_1(self, result):

        ig, qg, ie, qe = result.get_data()

        original_data_g = pg.ScatterPlotItem(ig, qg, brush=(100, 149, 237, 100), fillOutline=False)
        original_data_e = pg.ScatterPlotItem(ie, qe, brush=(255, 185, 15, 100))
        self.plt1.addItem(original_data_g)
        self.plt1.addItem(original_data_e)
        self.plt1.setAspectLocked()

    def _generate_plot_2(self, result):

        ig_rotated, qg_rotated, ie_rotated, qe_rotated = result.get_rotated_data()
        rotated_data_g = pg.ScatterPlotItem(ig_rotated, qg_rotated, brush=(100, 149, 237, 100))
        rotated_data_e = pg.ScatterPlotItem(ie_rotated, qe_rotated, brush=(255, 185, 15, 100))
        self.plt2.addItem(rotated_data_g)
        self.plt2.addItem(rotated_data_e)
        self.plt2.setAspectLocked()

    def _generate_plot_3(self, result):

        ig_hist_y, ig_hist_x = np.histogram(result.ig_rotated, bins=80)
        ie_hist_y, ie_hist_x = np.histogram(result.ie_rotated, bins=80)



        self.plt3.plot(ig_hist_x, ig_hist_y, stepMode="center", fillLevel=0, fillOutline=False, brush=(0, 0, 0, 255))
        self.plt3.plot(ie_hist_x, ie_hist_y, stepMode="center", fillLevel=0, fillOutline=False, brush=(255, 255, 255, 150))
        self.threshold_line = self.plt3.addLine(x=result.threshold,
                                                label=f'{result.threshold:.2f}',
                                                labelOpts={'position': 0.95},
                                                pen={'color': 'white', 'dash': [20, 20]})


    def _generate_plot_4(self, result):

        img = pg.ImageItem(image=result.confusion_matrix(), rect=[1, 1, 1, 1])
        img.setColorMap('viridis')
        self.plt4.addItem(img)
        self.plt4.invertY(True)
        self.plt4.setAspectLocked()
        self.plt4.showAxes(True)


        # all of this needs relabelling to prep_g, meas_g ... etc

        gg_label = pg.TextItem('|g>', anchor=(1, 0.5))
        ge_label = pg.TextItem('|g>', anchor=(0.5, 0))
        eg_label = pg.TextItem('|e>', anchor=(1, 0.5))
        ee_label = pg.TextItem('|e>', anchor=(0.5, 0))

        # anchor so we set the centre position of the text rather than the top left
        gg_fid_label = pg.TextItem(f'{100 * result.gg:.2f}%', color=(0, 0, 0), anchor=(0.5, 0.5))
        ge_fid_label = pg.TextItem(f'{100 * result.ge:.2f}%', color=(255, 255, 255), anchor=(0.5, 0.5))
        eg_fid_label = pg.TextItem(f'{100 * result.eg:.2f}%', color=(255, 255, 255), anchor=(0.5, 0.5))
        ee_fid_label = pg.TextItem(f'{100 * result.ee:.2f}%', color=(0, 0, 0), anchor=(0.5, 0.5))

        gg_label.setPos(1, 1.25)
        ge_label.setPos(1.25, 2)
        eg_label.setPos(1, 1.75)
        ee_label.setPos(1.75, 2)

        gg_fid_label.setPos(1.25, 1.25)
        ge_fid_label.setPos(1.75, 1.25)
        eg_fid_label.setPos(1.25, 1.75)
        ee_fid_label.setPos(1.75, 1.75)

        x_axis = self.plt4.getAxis('bottom')
        y_axis = self.plt4.getAxis('left')

        x_axis.setRange(1, 2)
        y_axis.setRange(1, 2)

        self.plt4.setXRange(1, 2)
        self.plt4.setYRange(1, 2)

        x_axis.setLabel('Measured')
        y_axis.setLabel('Prepared')

        x_axis.setTicks([[(1.25, '|g>'), (1.75, '|e>')]])
        y_axis.setTicks([[(1.25, '|g>'), (1.75, '|e>')]])

        self.plt4.addItem(gg_fid_label)
        self.plt4.addItem(ge_fid_label)
        self.plt4.addItem(eg_fid_label)
        self.plt4.addItem(ee_fid_label)


    def func(self):

        self.clear_plots()

        index = self.qubit_list.currentIndex()
        result = self.results_dataclasses[index]

        self._generate_plot_1(result)
        self._generate_plot_2(result)
        self._generate_plot_3(result)
        self._generate_plot_4(result)

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
