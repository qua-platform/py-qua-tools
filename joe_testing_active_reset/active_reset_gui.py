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
        self.initUI()
        self._populate_list()


    def initUI(self):

        hbox = QHBoxLayout(self)

        # create some widgets

        self.left = pg.LayoutWidget()
        self.right = pg.LayoutWidget()

        self.qubit_list = QComboBox()

        self.info_box = pg.TableWidget(3, 3)

        self.info_box.setData([
            ['', 'Passive', 'Active'],
            ['Fidelity', '98%', '85%'],
            ['Time', '100 ns', '90 ns']
        ])


        self.graphics_window = pg.GraphicsLayoutWidget()
        self.plt1 = self.graphics_window.addPlot(title='<font size="+1"><b>Passive reset</b></font>')
        self.plt2 = self.graphics_window.addPlot(title='<font size="+1"><b>Active reset</b></font>')

        self.left.addWidget(self.qubit_list, 0, 0)
        self.left.addWidget(self.info_box, 1, 0)
        self.left.addWidget(QFrame(), 2, 0)

        self.info_box.horizontalHeader().setVisible(False)
        self.info_box.verticalHeader().setVisible(False)

        self.right.addWidget(self.graphics_window)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.left)
        splitter.addWidget(self.right)

        # width of table + 3 pixels means we do not get a horizontal scroll bar. +3 to prevent
        # wider characters bringing a scroll bar in
        table_size = self.info_box.sizeHint()
        first_col_width = table_size.width() + 3
        splitter.setSizes([first_col_width + 3, 950])
        self.info_box.setMaximumHeight(int(table_size.height() * (3/4)))
        self.info_box.setShowGrid(False)


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