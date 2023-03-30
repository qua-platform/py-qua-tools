import pyqtgraph as pg
import numpy as np

from PyQt5.QtWidgets import *


def generate_color(value):
    """
    Generates RBG color on a smooth scale from 0 = red to 1 = green
    @param value: the value of the parameter (0 <= value <= 1)
    @return: the RGB tuple (0<->255, 0<->255, 0)
    """
    return (255 * (1 - value), 255 * value, 0.0)


class TextWidget(pg.PlotWidget):
    def __init__(
        self, name, value, parent=None, background="default", plotItem=None, **kargs
    ):
        """
        A widget that displays the 'value' parameter as a string in the centre of the viewing window.
        @param name: the widget's name
        @param value: the string/number that will be plotted
        @param parent: the parent widget
        @param background:
        @param plotItem:
        @param kargs:
        """
        super().__init__(
            name=name, parent=parent, background=background, plotItem=plotItem, **kargs
        )

        self.setTitle(name)
        self.hideAxis("bottom")
        self.hideAxis("left")
        self.setMouseEnabled(x=False, y=False)

        # color = generate_color(value)
        self.text = pg.TextItem(f"{value}", anchor=(0.5, 0.5))  # , color=color)

        self.addItem(self.text)

    def set_data(self, value, *args):
        """
        Set the plotted string's value
        @param value:
        @param args:
        @return:
        """
        self.text.setText(value)


class ViewerWidget(pg.PlotWidget):
    def __init__(
        self,
        name,
        dimensionality,
        parent=None,
        background="default",
        plotItem=None,
        **kargs,
    ):
        """
        A widget to display either 1d or 2d data, with methods to update the data as required.
        Includes crosshairs when the mouse is hovered over it, and also shows the x/y coordinates on
        the title when the mouse is hovering. Double clicking will print the x/y value to the ipython console
        in which the widget is being run.

        @param name: the widget's name
        @param dimensionality: the dimensionality of the data so we can use the correct method for updating data if required
        @param parent: this widget's parent widget
        @param background:
        @param plotItem:
        @param kargs:
        """
        super().__init__(
            name=name, parent=parent, background=background, plotItem=plotItem, **kargs
        )

        self.name = name
        self.dimensionality = dimensionality
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)

        self.addItem(self.vLine, ignoreBounds=True)
        self.addItem(self.hLine, ignoreBounds=True)

        self.lines = [self.hLine, self.vLine]
        [line.hide() for line in self.lines]

        self.setTitle(name)
        self.hideAxis("bottom")
        self.hideAxis("left")

    def set_data(self, x, y, z=None):
        """
        Set the data in the widget. Automatically updates 1 or 2d data (line plot vs image display) based on parameters
        @param x: x data
        @param y: y data
        @param z: z data, optional - will display 2d plot if provided.
        @return:
        """

        self.showAxis("bottom")
        self.showAxis("left")

        if z is None:
            if hasattr(self, "plot_item"):
                self.plot_item.setData(x, y)
            else:
                self.plot_item = self.plot(x, y)

        else:
            pos = (np.min(x), np.min(y))

            # scale from pixel index values to x/y values
            scale = (
                np.max(x) - np.min(x),
                np.max(y) - np.min(y),
            ) / np.array(z.shape)

            if hasattr(self, "plot_item"):
                self.plot_item.setImage(z)
                self.plot_item.resetTransform()
                self.plot_item.translate(*pos)
                self.plot_item.scale(*scale)

            else:
                self.plot_item = pg.ImageItem(image=z)
                self.addItem(self.plot_item)
                self.plot_item.translate(*pos)
                self.plot_item.scale(*scale)


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
            self.setTitle(f"{mousePoint.x():.2f}, {mousePoint.y():.2f}")

    def mouseDoubleClickEvent(self, ev):
        """On double click, the x/y value of the data will be printed to the console"""
        mouse_point = self.plotItem.vb.mapSceneToView(ev.pos())
        print(f"x: {mouse_point.x()}, y: {mouse_point.y()}")


class StackedWidget(QFrame):
    def __init__(self, qubit_name):
        """
        A widget container that has multiple plots, but only displays one at a time. A list is generated
        which contains the names of the widget layers. When the layer is clicked in the list, that layer
        is displayed.
        @param qubit_name: a name for the widget which is displayed as a title on all the plots.
        """
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

        self.layer_list.model().rowsInserted.connect(self.display_latest)

    def display_latest(self):
        self.display(len(self.layer_list) - 1)

    def add_0d_plot(self, name, text):
        self._add_layer(name, text)

    def add_1d_plot(self, name, x, y):
        self._add_layer(name, x, y)

    def add_2d_plot(self, name, x, y, z):
        self._add_layer(name, x, y, z)

    def _add_layer(self, name, x, y=None, z=None):

        assert (
            name not in self._get_layer_names()
        ), "Cannot use duplicate names for layers"

        if y is None and z is None:
            widget = TextWidget(self.name, x)
        else:
            widget = ViewerWidget(name=self.name, dimensionality=1)
            widget.set_data(x, y, z)

        self.Stack.addWidget(widget)
        self.layer_list.insertItem(len(self.layer_list), name)

        # resize each time we add a new member to the list
        self.layer_list.setMaximumWidth(int(self.layer_list.sizeHintForColumn(0) * 1.2))

    def display(self, i):
        self.Stack.setCurrentIndex(i)

    def update_layer_data(self, layer_name, x=None, y=None, z=None):

        widget = self.get_layer(layer_name)
        widget.set_data(x, y, z)

    def get_layer(self, name):
        index = self._get_layer_names().index(name)
        return self.Stack.widget(index)

    def _get_layer_names(self):
        return [self.layer_list.item(x).text() for x in range(self.layer_list.count())]
