import sys

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QApplication


# class CrosshairPlotWidget(pg.PlotWidget):
#
#     def __init__(self, parent=None, background='default', plotItem=None, **kargs):
#         super().__init__(parent=parent, background=background, plotItem=plotItem, **kargs)
#         self.vLine = pg.InfiniteLine(angle=90, movable=False)
#         self.hLine = pg.InfiniteLine(angle=0, movable=False)
#         self.addItem(self.vLine, ignoreBounds=True)
#         self.addItem(self.hLine, ignoreBounds=True)
#         self.hLine.hide()
#         self.vLine.hide()
#
#     def leaveEvent(self, ev):
#         """Mouse left PlotWidget"""
#         self.hLine.hide()
#         self.vLine.hide()
#
#     def enterEvent(self, ev):
#         """Mouse enter PlotWidget"""
#         self.hLine.show()
#         self.vLine.show()
#
#     def mouseMoveEvent(self, ev):
#         """Mouse moved in PlotWidget"""
#         if self.sceneBoundingRect().contains(ev.pos()):
#             mousePoint = self.plotItem.vb.mapSceneToView(ev.pos())
#             self.vLine.setPos(mousePoint.x())
#             self.hLine.setPos(mousePoint.y())
#
#
# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#
#     x = [0, 1, 2, 3, 4, 5]
#     y = np.random.normal(size=6)
#     plot = CrosshairPlotWidget()
#     plot.plot(x, y)
#     plot.show()
#
#     app.exec()

import sys
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from gui.widget import ViewerWidgetOld


# class stackedExample(QWidget):
#
#     def __init__(self):
#         super(stackedExample, self).__init__()
#         self.leftlist = QListWidget()
#
#         self.leftlist.insertItem(0, 'Contact')
#         self.leftlist.insertItem(1, 'Personal')
#         self.leftlist.insertItem(2, 'Educational')
#
#         self.stack1 = QWidget()
#         self.stack2 = QWidget()
#         self.stack3 = QWidget()
#
#         self.stack1UI()
#         self.stack2UI()
#         self.stack3UI()
#
#         self.Stack = QStackedWidget(self)
#         self.Stack.addWidget(self.stack1)
#         self.Stack.addWidget(self.stack2)
#         self.Stack.addWidget(self.stack3)
#
#         hbox = QHBoxLayout(self)
#         hbox.addWidget(self.leftlist)
#         hbox.addWidget(self.Stack)
#
#         self.setLayout(hbox)
#         self.leftlist.currentRowChanged.connect(self.display)
#         self.setGeometry(300, 50, 10, 10)
#         self.setWindowTitle('StackedWidget demo')
#         self.show()
#
#
#     def stack1UI(self):
#         layout = QFormLayout()
#         layout.addRow("Name", QLineEdit())
#         layout.addRow("Address", QLineEdit())
#         # self.setTabText(0,"Contact Details")
#         self.stack1.setLayout(layout)
#
#
#     def stack2UI(self):
#         layout = QFormLayout()
#         sex = QHBoxLayout()
#         sex.addWidget(QRadioButton("Male"))
#         sex.addWidget(QRadioButton("Female"))
#         layout.addRow(QLabel("Sex"), sex)
#         layout.addRow("Date of Birth", QLineEdit())
#
#         self.stack2.setLayout(layout)
#
#
#     def stack3UI(self):
#         layout = QHBoxLayout()
#         layout.addWidget(QLabel("subjects"))
#         layout.addWidget(QCheckBox("Physics"))
#         layout.addWidget(QCheckBox("Maths"))
#         self.stack3.setLayout(layout)
#
#
#     def display(self, i):
#         self.Stack.setCurrentIndex(i)


class StackedWidget(QWidget):

    def __init__(self):
        super(StackedWidget, self).__init__()
        self.leftlist = QListWidget()
        self.leftlist.insertItem(0, 'one')
        self.leftlist.insertItem(1, 'two')
        self.leftlist.insertItem(2, 'three')
        self.leftlist.setMaximumWidth(self.leftlist.minimumSizeHint().width())

        self.stack1 = ViewerWidgetOld(name='2d measure')
        self.stack2 = ViewerWidgetOld(name='1d trace')
        self.stack3 = ViewerWidgetOld(name='2d also ')

        self.stack1.set_data(np.random.rand(100, 100), dimensionality=2)
        self.stack2.set_data(np.stack([np.linspace(0, 1, 100), np.random.rand(100)]).T, dimensionality=1)
        self.stack3.set_data(np.random.rand(100, 100), dimensionality=2)

        # self.stack1UI()
        # self.stack2UI()
        # self.stack3UI()

        self.Stack = QStackedWidget(self)
        self.Stack.addWidget(self.stack1)
        self.Stack.addWidget(self.stack2)
        self.Stack.addWidget(self.stack3)

        hbox = QHBoxLayout(self)
        hbox.addWidget(self.leftlist, stretch=1)
        hbox.addWidget(self.Stack)

        self.setLayout(hbox)
        self.leftlist.currentRowChanged.connect(self.display)
        self.setGeometry(40, 30, 400, 300)
        self.setWindowTitle('StackedWidget demo')
        self.show()


    def stack1UI(self):
        layout = QFormLayout()
        self.stack1.setLayout(layout)


    def stack2UI(self):
        pass


    def stack3UI(self):
        layout = QHBoxLayout()
        layout.addWidget(QLabel("subjects"))
        layout.addWidget(QCheckBox("Physics"))
        layout.addWidget(QCheckBox("Maths"))
        self.stack3.setLayout(layout)


    def display(self, i):
        self.Stack.setCurrentIndex(i)



def main():
    app = QApplication(sys.argv)
    ex = StackedWidget()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()