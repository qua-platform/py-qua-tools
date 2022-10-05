from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QListWidget, QLineEdit, QTabWidget, QGridLayout, QVBoxLayout

import pyqtgraph as pg
from pyqtgraph.Qt import QT_LIB, QtCore, QtGui, QtWidgets
import exampleLoaderTemplate_generic as ui_template

from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

class App(QWidget):

    def __init__(self, results_dataclasses):

        super().__init__()

        self.resize(1000, 800)

        mainLayout = QGridLayout()

        vLayout1 = QVBoxLayout()

        # first tab
        self.tab1 = QWidget()


        # self.tab1.layout.addWidget(self.qb_list, 3, 0, 1,2 )

        self.tab1.ui = ui_template.Ui_Form()
        # self.tab1.setCentralWidget(self.tab1)
        self.tab1.ui.setupUi(self.tab1)

        # self.tab1.setLayout(self.tab1.layout)
        # second tab
        self.tab2 = QWidget()

        self.tabs = QTabWidget()

        self.tabs.addTab(self.tab1, 'Readout viewer')
        self.tabs.addTab(self.tab2, 'all viewer')

        mainLayout.addWidget(self.tabs, 0, 0)
        self.setLayout(mainLayout)


        self.setWindowTitle("Readout viewer")

        app = QtWidgets.QApplication.instance()
        policy = QtWidgets.QSizePolicy.Policy.Expanding

        self.results_dataclasses = results_dataclasses

        self.curListener = None
        self.itemCache = []

        self.resize(1200, 800)
        self.show()
        self.tab1.ui.splitter.setSizes([250, 950])

        for i in range(1, len(results_dataclasses) + 1):
            self.tab1.ui.qubitsList.addItem(
                'Qubit {}'.format(i)
            )

        self.tab1.ui.qubitsList.itemDoubleClicked.connect(self.printer)

    def printer(self):
        qubit_idx = self.tab1.ui.qubitsList.currentRow()

        results = self.results_dataclasses[qubit_idx]

        angle, threshold, fidelity, gg, ge, eg, ee = results.get_params()
        ig, qg, ie, qe = results.get_data()
        ig_rotated, qg_rotated, ie_rotated, qe_rotated = results.get_rotated_data()

        mw = MatplotlibWidget(parent=self.tab1.ui.readoutViewer)

        scatter = mw.getFigure().add_subplot(221)
        rotated_scatter = mw.getFigure().add_subplot(222)
        hist = mw.getFigure().add_subplot(223)
        matrix = mw.getFigure().add_subplot(224)

        scatter.plot(ig, qg, '.', alpha=0.1, markersize=2, label='Ground')
        scatter.plot(ie, qe, '.', alpha=0.1, markersize=2, label='Excited')
        scatter.axis("equal")
        scatter.legend(["Ground", "Excited"], loc='lower right')
        scatter.set_xlabel("I")
        scatter.set_ylabel("Q")
        scatter.set_title("Original Data")

        rotated_scatter.plot(ig_rotated, qg_rotated, ".", alpha=0.1, label="Ground", markersize=2)
        rotated_scatter.plot(ie_rotated, qe_rotated, ".", alpha=0.1, label="Excited", markersize=2)
        rotated_scatter.axis("equal")
        rotated_scatter.set_xlabel("I")
        rotated_scatter.set_ylabel("Q")
        rotated_scatter.set_title("Rotated Data")

        hist.hist(ig_rotated, bins=50, alpha=0.75, label="Ground")
        hist.hist(ie_rotated, bins=50, alpha=0.75, label="Excited")
        hist.axvline(x=threshold, color="k", ls="--", alpha=0.5)
        text_props = dict(
            horizontalalignment="center",
            verticalalignment="center",
            transform=hist.transAxes
        )
        hist.text(0.7, 0.9, f"{threshold:.3e}", text_props)
        hist.set_xlabel("I")
        hist.set_title("1D Histogram")

        matrix.imshow(results.confusion_matrix())
        matrix.set_xticks([0, 1])
        matrix.set_yticks([0, 1])
        matrix.set_xticklabels(labels=["|g>", "|e>"])
        matrix.set_yticklabels(labels=["|g>", "|e>"])
        matrix.set_ylabel("Prepared")
        matrix.set_xlabel("Measured")
        matrix.text(0, 0, f"{100 * gg:.1f}%", ha="center", va="center", color="k")
        matrix.text(1, 0, f"{100 * ge:.1f}%", ha="center", va="center", color="w")
        matrix.text(0, 1, f"{100 * eg:.1f}%", ha="center", va="center", color="w")
        matrix.text(1, 1, f"{100 * ee:.1f}%", ha="center", va="center", color="k")
        matrix.set_title("Fidelities")

        mw.getFigure().tight_layout()
        mw.draw()

        self.tab1.ui.readoutViewer.addWidget(
            mw, 0, 0
        )
