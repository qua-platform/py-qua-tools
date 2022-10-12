import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import numpy as np

class ActiveResetGUI(QWidget):
    def __init__(self, num_qubits):

        self.num_qubits = num_qubits
        super(ActiveResetGUI, self).__init__()
        self.initialise_ui()
        self._populate_list()


    def initialise_ui(self):

        hbox = QHBoxLayout(self)

        # create some widgets

        self.left = pg.LayoutWidget()
        self.right = pg.LayoutWidget()

        self.qubit_list = QComboBox()

        self.info_box = pg.TableWidget(3, 3)


        self.info_box.setData(self.generate_table(98, 86, 100e-9, 90e-9))


        self.graphics_window = pg.GraphicsLayoutWidget()
        self.plt1 = self.graphics_window.addPlot(title='<font size="+1"><b>Passive reset IQ</b></font>')
        self.plt2 = self.graphics_window.addPlot(title='<font size="+1"><b>Active reset IQ</b></font>')

        self.graphics_window.nextRow()
        self.plt3 = self.graphics_window.addPlot(title='<font size="+1"><b>1D histogram</b></font>')
        self.plt4 = self.graphics_window.addPlot(title='<font size="+1"><b>1D histogram</b></font>')


        self.left.addWidget(self.qubit_list, 0, 0)
        self.left.addWidget(self.info_box, 1, 0)
        self.left.addWidget(QFrame(), 2, 0)

        self.info_box.horizontalHeader().setVisible(False)
        self.info_box.verticalHeader().setVisible(False)


        self.right.addWidget(self.graphics_window)


        # width of table + 3 pixels means we do not get a horizontal scroll bar. +3 to prevent
        # wider characters bringing a scroll bar in
        table_size = self.info_box.sizeHint()
        self.info_box.setMaximumHeight(int(table_size.height() * (3/4)))
        self.info_box.setMaximumWidth(int(table_size.width() * (3/4)))
        self.info_box.setShowGrid(False)

        self.ground_state_colour = (100, 149, 237)
        self.excited_state_colour = (255, 185, 15)



        hbox.addWidget(self.left)
        hbox.addWidget(self.right)

        self.setLayout(hbox)

        QApplication.setStyle(QStyleFactory.create('Cleanlooks'))

        self.setGeometry(100, 100, 1200, 500)
        self.setWindowTitle('Qubit reset comparison')

        # self.qubit_list.itemDoubleClicked.connect(self.func)
        self.qubit_list.currentIndexChanged.connect(self.update_plots)


        self.show()

    def generate_fake_histograms(self, a, b):
        ## make interesting distribution of values
        vals1 = np.random.normal(size=500)
        vals2 = np.random.normal(size=260, loc=4)
        ## compute standard histogram
        y, x = np.histogram(vals1, bins=np.linspace(-3, 8, 80))
        y2, x2 = np.histogram(vals2, bins=np.linspace(-3, 8, 80))
        return a * y, x, b * y2, x2

    def generate_random_table_data(self):

        pf, af = np.random.rand(2) * 100
        pt, at = np.random.rand(2) / 5e8

        return pf, pt, af, at

    def generate_table(self, pf, pt, af, at):
        table_data = [
            ['', 'Passive', 'Active'],
            ['Fidelity', f'{pf:.2f}%', f'{af:.2f}%'],
            ['Time', f'{(pt * 1e9):.2f} ns', f'{(at * 1e9):.2f} ns']
        ]

        return table_data

    def set_table(self, pf, pt, af, at):
        data = self.generate_table(pf, pt, af, at)
        self.info_box.setData(data)

    def _generate_plot_1(self):
        rotated_data_g = pg.ScatterPlotItem(
            np.random.normal(1, 0.2, 5000),
            np.random.normal(1, 0.2, 5000),
            brush=(*self.ground_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        rotated_data_e = pg.ScatterPlotItem(
            np.random.normal(1.5, 0.2, 5000),
            np.random.normal(1, 0.2, 5000),
            brush=(*self.excited_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        self.plt1.addItem(rotated_data_g)
        self.plt1.addItem(rotated_data_e)

        plt1_threshold = 1.25

        self.plt1.addLine(
            x=plt1_threshold,
            label=f'{plt1_threshold:.2f}, θ={(np.random.rand() * 1000) % 90:.2f}°',
            labelOpts={'position': 0.9},
            pen={'color': 'white', 'dash': [20, 20]}
        )

        self.plt1.setAspectLocked()

    def _generate_plot_2(self):


        rotated_data_g = pg.ScatterPlotItem(
            np.random.normal(1, 0.2, 5000),
            np.random.normal(1, 0.2, 5000),
            brush=(*self.ground_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        rotated_data_e = pg.ScatterPlotItem(
            np.random.normal(1.5, 0.2, 5000),
            np.random.normal(1, 0.2, 5000),
            brush=(*self.excited_state_colour, 100),
            symbol='s',
            size='2',
            pen=pg.mkPen(None)
        )

        self.plt2.addItem(rotated_data_g)
        self.plt2.addItem(rotated_data_e)

        plt2_threshold = 1.25

        self.plt2.addLine(
            x=plt2_threshold,
            label=f'{plt2_threshold:.2f}, θ={(np.random.rand() * 1000) % 90:.2f}°',
            labelOpts={'position': 0.9},
            pen={'color': 'white', 'dash': [20, 20]}
        )

        self.plt2.setAspectLocked()

    def _generate_plot_3(self):

        y, x, y2, x2 = self.generate_fake_histograms(1, 1)

        ## Using stepMode="center" causes the plot to draw two lines for each sample.
        ## notice that len(x) == len(y)+1
        self.plt3.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(*self.ground_state_colour, 200), pen=pg.mkPen(None))
        self.plt3.plot(x2, y2, stepMode="center", fillLevel=0, fillOutline=True, brush=(*self.excited_state_colour, 200), pen=pg.mkPen(None))

        plt3_threshold = np.mean([np.median(x), np.median(x2)]) + (0.2 * np.random.rand())

        self.plt3.addLine(
            x=plt3_threshold,
            label=f'{plt3_threshold:.2f}',
            labelOpts={'position': 0.95},
            pen={'color': 'white', 'dash': [20, 20]}
        )

    def _generate_plot_4(self):

        y, x, y2, x2 = self.generate_fake_histograms(0.2, 1.8)
        self.plt4.plot(x, y, stepMode="center", fillLevel=0, fillOutline=True, brush=(*self.ground_state_colour, 200), pen=pg.mkPen(None))
        self.plt4.plot(x2, y2, stepMode="center", fillLevel=0, fillOutline=True, brush=(*self.excited_state_colour, 200), pen=pg.mkPen(None))

        plt4_threshold = np.mean([np.median(x), np.median(x2)]) + (0.2 * np.random.rand())

        self.plt4.addLine(
            x=plt4_threshold,
            label=f'{plt4_threshold:.2f}',
            labelOpts={'position': 0.95},
            pen={'color': 'white', 'dash': [20, 20]}
        )

    def update_plots(self):

        self.plt1.clear()
        self.plt2.clear()
        self.plt3.clear()
        self.plt4.clear()

        self._generate_plot_1()
        self._generate_plot_2()
        self._generate_plot_3()
        self._generate_plot_4()

        self.set_table(*self.generate_random_table_data())


    def _populate_list(self):

        for i in range(self.num_qubits):
            self.qubit_list.addItem(
                f'Qubit {i + 1}'
            )



def main():
    app = QApplication(sys.argv)
    ex = ActiveResetGUI(32)
    # sys.exit(app.exec_())
    app.exec_()

if __name__ == '__main__':
    main()