import pyqtgraph as pg
import numpy as np
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
def fake_function(x):
    x0 = (np.random.rand()) * 0.8
    return 1 - (1 / (1 + ((x - x0) / 0.25) ** 2))


def fake_data():
    x = np.linspace(0, 1, 100)
    y = fake_function(x)
    y += np.random.rand(y.size) * 0.2
    return x * 1e6, y


def find_nearest(array, value):
    array = np.asarray(array)
    idx = (np.abs(array - value)).argmin()
    return idx


def generate_color(value):
    """
    Generates RBG color on a smooth scale from 0 = red to 1 = green
    @param value: the value of the parameter (0 <= value <= 1)
    @return: the RGB tuple (0<->255, 0<->255, 0)
    """
    return (255 * (1 - value), 255 * value, 0.)


class ViewerWidgetOld(pg.PlotWidget):

    def __init__(self, name, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(name=name, parent=parent, background=background, plotItem=plotItem, **kargs)

        self.name = name

        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)

        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)

        self.lines = [self.hLine, self.vLine]
        [line.hide() for line in self.lines]

        self.setTitle(name)
        self.hideAxis('bottom')
        self.hideAxis('left')

        self.hidden = True

        value = np.random.rand()
        color = generate_color(value)
        self.text = pg.TextItem(f'{value * 100:.2f}%', anchor=(0.5, 0.5), color=color)

        self.addItem(self.text)
        self.text.hide()

    def set_data(self, data, dimensionality):

        self.showAxis('bottom')
        self.showAxis('left')

        self.hidden = False

        if hasattr(self, 'plot_item'):

            if dimensionality == 1:
                self.plot_item.setData(data)

            else:
                self.plot_item.setImage(data)

        else:
            if dimensionality == 1:
                self.plot_item = self.plot(data)
            else:
                self.plot_item = pg.ImageItem(image=data)
                self.addItem(self.plot_item)

    def leaveEvent(self, ev):
        """Mouse left PlotWidget"""
        self.hLine.hide()
        self.vLine.hide()

        self.setTitle(self.name)

    def enterEvent(self, ev):
        """Mouse enter PlotWidget"""
        if not self.hidden:
            self.hLine.show()
            self.vLine.show()

    def mouseMoveEvent(self, ev):
        """Mouse moved in PlotWidget"""

        if self.sceneBoundingRect().contains(ev.pos()):
            mousePoint = self.plotItem.vb.mapSceneToView(ev.pos())
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())

            if not self.hidden:
                self.setTitle(f'{mousePoint.x():.2f}, {mousePoint.y():.2f}')

    def mouseDoubleClickEvent(self, ev):

        if not self.hidden:
            mousePoint = self.plotItem.vb.mapSceneToView(ev.pos())
            print(mousePoint.x())
            print(mousePoint.y())

        self.toggle_hide()

    def hide_plot(self):
        [line.hide() for line in self.lines]
        self.hideAxis('bottom')
        self.hideAxis('left')
        self.hideButtons()
        self.setMouseEnabled(False)

        if hasattr(self, 'plot_item'):
            self.plot_item.hide()

    def show_plot(self):

        [line.show() for line in self.lines]
        self.showAxis('bottom')
        self.showAxis('left')
        self.showButtons()
        self.setMouseEnabled(True)

        if hasattr(self, 'plot_item'):
            self.plot_item.show()

    def show_text(self):
        self.text.show()

    def hide_text(self):
        self.text.hide()

    def keyPressEvent(self, ev):
        """
        Remove the widget if the delete key is pressed while the widget is in mouse focus
        @param ev: key press event, containing the information about the press ∂
        @return:
        """
        if ev.key() == 16777223:
            self.hide()

    def toggle_hide(self):
        if self.hidden:
            self.show_plot()
            self.hide_text()
            self.autoRange()
            self.setMouseEnabled(x=True, y=True)

        else:
            self.hide_plot()
            self.show_text()
            self.setTitle(self.name)
            self.autoRange()
            self.setMouseEnabled(x=False, y=False)

        self.hidden = not self.hidden



class RadioButtons(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        layout = QGridLayout()
        self.setLayout(layout)

        radiobutton = QRadioButton("Australia")
        radiobutton.setChecked(True)
        radiobutton.country = "Australia"
        radiobutton.toggled.connect(self.onClicked)
        layout.addWidget(radiobutton, 0, 0)

        radiobutton = QRadioButton("China")
        radiobutton.country = "China"
        radiobutton.toggled.connect(self.onClicked)
        layout.addWidget(radiobutton, 0, 1)

        radiobutton = QRadioButton("Japan")
        radiobutton.country = "Japan"
        radiobutton.toggled.connect(self.onClicked)
        layout.addWidget(radiobutton, 0, 2)



    def onClicked(self):
        radioButton = self.sender()
        if radioButton.isChecked():
            print("Country is %s" % (radioButton.country))


    def leaveEvent(self, ev):
        """Mouse left PlotWidget"""
        self.hide()
    def enterEvent(self, ev):
        """Mouse enter PlotWidget"""
        self.show()




class StackedWidget(QFrame):

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

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setLineWidth(1)
        self.add_layer()
    def add_layer(self):#, name, data):
        print(len(self.leftlist))
    def display(self, i):
        self.Stack.setCurrentIndex(i)
