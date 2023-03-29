import pyqtgraph as pg
import numpy as np
import time
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5 import QtGui


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


class TextWidget(pg.PlotWidget):

    def __init__(self, name, value, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(name=name, parent=parent, background=background, plotItem=plotItem, **kargs)

        self.setTitle(name)
        self.hideAxis('bottom')
        self.hideAxis('left')
        self.setMouseEnabled(x=False, y=False)

        # color = generate_color(value)
        self.text = pg.TextItem(f'{value}', anchor=(0.5, 0.5))#, color=color)

        self.addItem(self.text)


class ViewerWidget(pg.PlotWidget):

    def __init__(self, name, dimensionality, parent=None, background='default', plotItem=None, **kargs):
        super().__init__(name=name, parent=parent, background=background, plotItem=plotItem, **kargs)

        self.name = name
        self.dimensionality = dimensionality
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)

        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)

        self.lines = [self.hLine, self.vLine]
        [line.hide() for line in self.lines]

        self.setTitle(name)
        self.hideAxis('bottom')
        self.hideAxis('left')

    def set_data(self, data, x=None, y=None):

        self.showAxis('bottom')
        self.showAxis('left')

        if hasattr(self, 'plot_item'):

            if self.dimensionality == 1:
                self.plot_item.setData(data)

            elif self.dimensionality == 2:
                pos = (np.min(x), np.min(y))

                # scale from pixel index values to x/y values
                scale = (
                            np.max(x) - np.min(x),
                            np.max(y) - np.min(y),
                        ) / np.array(data.shape)

                self.plot_item.setImage(data, pos=pos, scale=scale)

        else:
            if self.dimensionality == 1:
                self.plot_item = self.plot(data)
            elif self.dimensionality == 2:
                
                pos = (np.min(x), np.min(y))

                # scale from pixel index values to x/y values
                scale = (
                            np.max(x) - np.min(x),
                            np.max(y) - np.min(y),
                        ) / np.array(data.shape)

                self.plot_item = pg.ImageItem(image=data, pos=pos, scale=scale)
                self.addItem(self.plot_item)

    def leaveEvent(self, ev):
        """Mouse left PlotWidget"""
        self.hLine.hide()
        self.vLine.hide()

        self.setTitle(self.name)

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

            # if not self.hidden:
            self.setTitle(f'{mousePoint.x():.2f}, {mousePoint.y():.2f}')

    def mouseDoubleClickEvent(self, ev):
        mouse_point = self.plotItem.vb.mapSceneToView(ev.pos())
        print(f'x: {mouse_point.x()}, y: {mouse_point.y()}')


class StackedWidget(QFrame):

    def __init__(self, qubit_name):
        super(StackedWidget, self).__init__()

        self.name = qubit_name
        self.layer_list = QListWidget()
        self.layer_list.setMaximumWidth(int(self.layer_list.sizeHintForColumn(0) * 1.2))


        self.Stack = QStackedWidget(self)
        hbox = QHBoxLayout(self)
        hbox.addWidget(self.layer_list, stretch=1)
        hbox.addWidget(self.Stack)

        self.setLayout(hbox)
        self.layer_list.currentRowChanged.connect(self.display)

        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setLineWidth(1)
        #
        # self.layer_list.model().rowsInserted.connect(self.display_latest)


    def add_0d_plot(self, name, text):
        self._add_layer(name, text, 0)

    def add_1d_plot(self, name, data):
        self._add_layer(name, data, 1)

    def add_2d_plot(self, name, data):
        self._add_layer(name, data, 2)

    def _add_layer(self, name, data, dimensionality):

        assert name not in self._get_layer_names(), 'Cannot use duplicate names for layers'

        self.layer_list.insertItem(len(self.layer_list), name)

        if dimensionality == 0:
            widget = TextWidget(self.name, data)
        else:
            widget = ViewerWidget(name=self.name, dimensionality=dimensionality)
            widget.set_data(data)
        self.Stack.addWidget(widget)

        # resize each time we add a new member to the list
        self.layer_list.setMaximumWidth(int(self.layer_list.sizeHintForColumn(0) * 1.2))

    def display(self, i):
        self.Stack.setCurrentIndex(i)
    def update_layer_data(self, layer_name, data):

        widget = self.get_layer(layer_name)
        widget.set_data(data)

    def get_layer(self, name):
        index = self._get_layer_names().index(name)
        return self.Stack.widget(index)

    def _get_layer_names(self):
        return [self.layer_list.item(x).text() for x in range(self.layer_list.count())]


