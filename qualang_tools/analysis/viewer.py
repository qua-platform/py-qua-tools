import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QListWidget, QLineEdit, QTabWidget, QGridLayout, QVBoxLayout
import pyqtgraph as pg

class App(QWidget):

    def __init__(self):

        super().__init__()

        self.resize(1000, 800)

        mainLayout = QGridLayout()

        vLayout1 = QVBoxLayout()

        # first tab
        self.tab1 = QWidget()
        self.tab1.layout = QGridLayout()
        self.tab1.layout.addWidget(QLabel('test'))

        self.qb_list = QListWidget()
        self.readoutViewer = pg.LayoutWidget()

        self.tab1.layout.addWidget(self.qb_list, 3, 0, 1,2 )



        self.tab1.setLayout(self.tab1.layout)
        # second tab
        self.tab2 = QWidget()

        self.tabs = QTabWidget()

        self.tabs.addTab(self.tab1, 'Readout viewer')
        self.tabs.addTab(self.tab2, 'all viewer')

        mainLayout.addWidget(self.tabs, 0, 0)
        self.setLayout(mainLayout)

app = QApplication(sys.argv)
demo = App()
demo.show()

sys.exit(app.exec())
