import pyqtgraph as pg
from pyqtgraph.Qt import QT_LIB, QtCore, QtGui, QtWidgets
import exampleLoaderTemplate_generic as ui_template
from argparse import Namespace
from collections import OrderedDict
import numpy as np
from pyqtgraph.widgets.MatplotlibWidget import MatplotlibWidget

class multiQubitReadoutPresenter(QtWidgets.QMainWindow):

    def __init__(self, results_dataclasses):
        QtWidgets.QMainWindow.__init__(self)
        self.ui = ui_template.Ui_Form()
        self.cw = QtWidgets.QWidget()
        self.setCentralWidget(self.cw)
        self.ui.setupUi(self.cw)
        self.setWindowTitle("Readout viewer")

        app = QtWidgets.QApplication.instance()
        policy = QtWidgets.QSizePolicy.Policy.Expanding

        self.results_dataclasses = results_dataclasses

        self.curListener = None
        self.itemCache = []
        # self.populateTree(self.ui.exampleTree.invisibleRootItem(), utils.examples_)
        # self.ui.exampleTree.expandAll()

        self.resize(1200, 800)
        self.show()
        self.ui.splitter.setSizes([250, 950])

        for i in range(1, len(results_dataclasses) + 1):
            self.ui.qubitsList.addItem(
                'Qubit {}'.format(i)
            )

        # self.oldText = self.ui.codeView.toPlainText()
        self.ui.loadBtn.clicked.connect(self.printer)
        # self.ui.exampleTree.currentItemChanged.connect(self.showFile)
        self.ui.qubitsList.itemDoubleClicked.connect(self.printer)
        # self.ui.codeView.textChanged.connect(self.onTextChange)
        # self.codeBtn.clicked.connect(self.runEditedCode)
        # self.updateCodeViewTabWidth(self.ui.codeView.font())

    def printer(self):
        qubit_idx = self.ui.qubitsList.currentRow()

        results = self.results_dataclasses[qubit_idx]

        angle, threshold, fidelity, gg, ge, eg, ee = results.get_params()
        ig, qg, ie, qe = results.get_data()

        # this should happen in the results dataclass not here
        C = np.cos(angle)
        S = np.sin(angle)
        # Condition for having e > Ig
        if np.mean((ig - ie) * C - (qg - qe) * S) > 0:
            angle += np.pi
            C = np.cos(angle)
            S = np.sin(angle)

        ig_rotated = ig * C - qg * S
        qg_rotated = ig * S + qg * C

        ie_rotated = ie * C - qe * S
        qe_rotated = ie * S + qe * C


        mw = MatplotlibWidget(parent=self.ui.readoutViewer)

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

        self.ui.readoutViewer.addWidget(
            mw, 0, 0
        )

        #
        # plot = self.ui.readoutViewer.addPlot(0, 0)
        # plot.plot(np.random.normal(size=100), np.random.normal(size=100))
        # plot = self.ui.readoutViewer.addPlot(0, 1)
        # plot.plot(np.random.normal(size=100), np.random.normal(size=100))
        # plot = self.ui.readoutViewer.addPlot(1, 0)
        # plot.plot(np.random.normal(size=100), np.random.normal(size=100))
        # plot = self.ui.readoutViewer.addPlot(1, 1)
        # plot.plot(np.random.normal(size=100), np.random.normal(size=100))




    # def showFile(self):
    #     fn = self.currentFile()
    #     text = self.getExampleContent(fn)
    #     self.ui.codeView.setPlainText(text)
    #     self.ui.loadedFileLabel.setText(fn)
    #     self.codeBtn.hide()

    def populateTree(self, root, examples):
        bold_font = None
        for key, val in examples.items():
            item = QtWidgets.QTreeWidgetItem([key])
            self.itemCache.append(item)  # PyQt 4.9.6 no longer keeps references to these wrappers,
            # so we need to make an explicit reference or else the .file
            # attribute will disappear.
            if isinstance(val, OrderedDict):
                self.populateTree(item, val)
            elif isinstance(val, Namespace):
                item.file = val.filename
                if 'recommended' in val:
                    if bold_font is None:
                        bold_font = item.font(0)
                        bold_font.setBold(True)
                    item.setFont(0, bold_font)
            else:
                item.file = val
            root.addChild(item)



def main():
    app = pg.mkQApp()
    loader = multiQubitReadoutPresenter()
    pg.exec()


