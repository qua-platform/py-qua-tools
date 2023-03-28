import sys

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication


class CrosshairPlotWidget(pg.PlotWidget):

    def __init__(self, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(parent=parent, background=background, plotItem=plotItem, **kargs)
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)
        self.hLine.hide()
        self.vLine.hide()

    def leaveEvent(self, ev):
        """Mouse left PlotWidget"""
        self.hLine.hide()
        self.vLine.hide()

    def enterEvent(self, ev):
        """Mouse enter PlotWidget"""
        self.hLine.show()
        self.vLine.show()

    def mouseMoveEvent(self, ev):
        """Mouse moved in PlotWidget"""
        if self.sceneBoundingRect().contains(ev.pos()):
            mousePoint = self.plotItem.vb.mapSceneToView(ev.pos())
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    x = [0, 1, 2, 3, 4, 5]
    y = np.random.normal(size=6)
    plot = CrosshairPlotWidget()
    plot.plot(x, y)
    plot.show()

    app.exec()