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
        self.setup_dashboard_tab()
        self._populate_list()
        self._list_by_fidelity()
        self.show()


    def setup_dashboard_tab(self):

        self.dashboard_tab_layout = QGridLayout()

        self.dashboard_tab.setLayout(self.dashboard_tab_layout)

        # widets

        self.dashboard_list = QListWidget()
        fidelity_average = QLabel(f'Average fidelity is {98}%')
        average_overlap = QLabel(f'Average overlap is {0.1}')

        self.dashboard_tab_layout.addWidget(self.dashboard_list, 0, 0, 2, 1)
        self.dashboard_tab_layout.addWidget(fidelity_average, 0, 1, 1, 5)
        self.dashboard_tab_layout.addWidget(average_overlap, 0, 6, 1, 5)
        self.dashboard_list.itemDoubleClicked.connect(self.switch_to_qubit_tab)

        self.dashboard_list.setMaximumWidth(200)


    def initialise_ui(self):

        main_layout = QGridLayout()

        self.readout_tab = QWidget()
        self.dashboard_tab = QWidget()

        self.tabs = QTabWidget()

        self.tabs.addTab(self.dashboard_tab, 'Dashboard')
        self.tabs.addTab(self.readout_tab, 'Qubits')

        box_layout = QHBoxLayout(self)

        self.readout_tab.setLayout(box_layout)

        self.ground_state_colour = (100, 149, 237)
        self.excited_state_colour = (255, 185, 15)

        # create some widgets

        self.left = pg.LayoutWidget()
        self.right = pg.LayoutWidget()

        self.qubit_list = QComboBox()

        self.key_layout = QVBoxLayout()
        self.key = QWidget()
        self.key.setLayout(self.key_layout)


        self.ground_state_label = QLabel('Ground state')
        self.excited_state_label = QLabel('Excited state')



        self.ground_state_label.setAlignment(Qt.AlignCenter)
        self.excited_state_label.setAlignment(Qt.AlignCenter)


        self.ground_state_label.setStyleSheet(f"background-color:rgb{self.ground_state_colour}; border-radius:5px")
        self.excited_state_label.setStyleSheet(f"background-color:rgb{self.excited_state_colour}; border-radius:5px")

        self.key_layout.addWidget(self.ground_state_label)
        self.key_layout.addWidget(self.excited_state_label)

        self.graphics_window = pg.GraphicsLayoutWidget()
        self.plt1 = self.graphics_window.addPlot(title='<font size="+1"><b>Original data</b></font>')
        self.plt2 = self.graphics_window.addPlot(title='<font size="+1"><b>Rotated data</b></font>')
        self.graphics_window.nextRow()
        self.plt3 = self.graphics_window.addPlot(title='<font size="+1"><b>1D Histogram</b></font>')
        self.plt4 = self.graphics_window.addPlot(title='<font size="+1"><b>Fidelities</b></font>')

        self.left.addWidget(self.qubit_list, 0, 0)
        self.left.addWidget(self.key, 1, 0)
        # add a blank frame to take up some space so the state key labels aren't massive
        self.left.addWidget(QFrame(), 2, 0, 3, 1)

        self.right.addWidget(self.graphics_window)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)


        box_layout.addWidget(splitter)
        main_layout.addWidget(self.tabs, 0, 0)

        self.setLayout(main_layout)

        # self.layout().addWidget(self.tabs)

        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))

        self.setGeometry(100, 100, 1100, 700)
        self.setWindowTitle('Readout viewer')

        self.qubit_list.currentIndexChanged.connect(self.update_plots)


    def switch_to_qubit_tab(self):

        unsorted_qubit_id = self.dashboard_list.currentRow()
        qubit_id = self.sorted_qubit_ids[unsorted_qubit_id]

        self.qubit_list.setCurrentIndex(qubit_id)
        self.update_plots()
        self.tabs.setCurrentIndex(1)


    def clear_plots(self):
        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt4.clear()

    def _generate_plot_1(self, result):

        ig, qg, ie, qe = result.get_data()

        original_data_g = pg.ScatterPlotItem(
            ig,
            qg,
            brush=(*self.ground_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        original_data_e = pg.ScatterPlotItem(
            ie,
            qe,
            brush=(*self.excited_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )


        self.plt1.addItem(original_data_g)
        self.plt1.addItem(original_data_e)
        self.plt1.setAspectLocked()

    def _generate_plot_2(self, result):

        ig_rotated, qg_rotated, ie_rotated, qe_rotated = result.get_rotated_data()

        rotated_data_g = pg.ScatterPlotItem(
            ig_rotated,
            qg_rotated,
            brush=(*self.ground_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        rotated_data_e = pg.ScatterPlotItem(
            ie_rotated,
            qe_rotated,
            brush=(*self.excited_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        self.plt2.addItem(rotated_data_g)
        self.plt2.addItem(rotated_data_e)
        self.plt2.setAspectLocked()

    def _generate_plot_3(self, result):

        ig_hist_y, ig_hist_x = np.histogram(result.ig_rotated, bins=80)
        ie_hist_y, ie_hist_x = np.histogram(result.ie_rotated, bins=80)



        self.plt3.plot(
            ig_hist_x, ig_hist_y,
            stepMode="center",
            fillLevel=0,
            fillOutline=False,
            brush=(*self.ground_state_colour, 255),
            pen=pg.mkPen(None)
        )

        self.plt3.plot(
            ie_hist_x, ie_hist_y,
            stepMode="center",
            fillLevel=0,
            fillOutline=False,
            brush=(*self.excited_state_colour, 150),
            pen=pg.mkPen(None)
        )

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


    def update_plots(self):

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

    def _list_by_fidelity(self):

        unsorted_qubit_fidelities = [result.fidelity for result in self.results_dataclasses]
        qubit_names = [f'Qubit {i}' for i in range(1, self.num_qubits + 1)]
        qubit_ids = range(0, self.num_qubits)
        # out = [(fid, x) for fid, x in sorted(zip(unsorted_qubit_list, qubit_names), key=lambda pair: pair[0])]
        # print(out)

        self.sorted_qubit_ids = [id for fid, id in sorted(zip(unsorted_qubit_fidelities, qubit_ids), key=lambda pair: pair[0])][::-1]

        for fidelity, qubit_name in sorted(zip(unsorted_qubit_fidelities, qubit_names), key=lambda pair: pair[0])[::-1]:
            self.dashboard_list.addItem(f"{qubit_name:<9} ({fidelity:.2f}%)")






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
