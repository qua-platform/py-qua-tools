import pyqtgraph as pg
import numpy as np
import time


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


# if data.shape[1] == 2:
#     # self.plot_item = self.plot(data)
#     self.dimensionality = 1
#
# else:
#     # self.plot_item = pg.ImageItem(image=data)
#     # self.addItem(self.plot_item)
#     self.dimensionality = 2


class ViewerWidget(pg.PlotWidget):



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
