"""
Created on 16/09/2021
@author jdh
@author bvs
"""

import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui
from pyqtgraph.dockarea import *
import sys
from pathlib import Path, PosixPath
from multiprocessing import Process
import pyqtgraph.exporters
from logging import getLogger
import numpy as np
# from qgor.plotters.Plot_Widgets import Dock as CustomDock
from datetime import date
from time import gmtime, strftime

from .widget import Plot_1D_Widget
from PyQt5.QtGui import QIcon

import json


def load_json(path):
    """
    a function to load a json
    @param path: the path of the json to load
    @return: the json as a dict
    """
    with open(path) as f:
        return json.load(f)

def save_json(path, dict):
    """
    a function to load a json
    @param path: the path of the json to load
    @return: the json as a dict
    """
    # if the file already exists, load it and add to the dict to be saved
    if path.is_file():
        dict = {**load_json(path=path), **dict}

    with open(path, "w") as f:
        json.dump(dict, f, indent=4, sort_keys=False)

logger = getLogger(__name__)

def get_widget_axis_centres(widget):
    centres = np.array(
        [widget.x_mm[-1] + widget.x_mm[0],
         widget.y_mm[-1] + widget.y_mm[0]]
    ) / 2

    return centres


class Plotter_Base:
    def __init__(
            self,
            folder,
            axis,
            mode="read",
            options_path=Path(__file__).parent / "plotter.json",
            additional_metadata_dict={}
    ):
        """
        Initialise the plotter window and generate the first plots
        @param folder: The data folder that contains the measurement data
        @param axis: The combinations of variables to plot. A list of tuples. Each tuple contains
                      either two or three elements for either a 1D or 2D plot.
        """

        self.folder = folder
        self.axis = axis
        self.additional_metadata_dict = additional_metadata_dict

        # duplicate parameter names cause a bug in the plotter. This removes that possibility.
        for i, ax in enumerate(axis):
            assert_message = (
                "{} contains a duplicate parameter name. Consider renaming it!".format(
                    ax
                )
            )
            # if length of set == length of list then there are no duplicates.
            if not set(ax).__len__() == ax.__len__():
                logger.warning(assert_message)

        # loading the json options
        self.options_path = options_path

        # loading the plot_options
        self.options = load_json(self.options_path)

        self.screenshot_saved = False

    def save(self):

        type_action_mapping = {
            PosixPath: lambda x: str(x.resolve()),
        }

        do_not_save = ["mm_w", "mm_r", "folder", "options_path", "options", "process", 'processors', 'variables']

        data = {}
        for key, value in self.__dict__.items():
            if key not in do_not_save:
                class_hash = type(value)
                action = type_action_mapping.get(class_hash, lambda x: x)
                data[key] = action.__call__(value)

        # add some other things to the meta data
        data['time_of_measurement'] = strftime("%a, %d %b %Y %H:%M:%S +0000", gmtime())

        save_json(self.folder / "meta_data.json", data)

    def get_data(self):
        return {
            variable: self.mm_r.__getattribute__(variable)
            for variable in self.mm_r.units.keys()
        }

    def get_plots_data(self):
        return [
            tuple(self.mm_r.__getattribute__(name) for name in ax) for ax in self.axis
        ]

    def plot(self):
        self.process = Process(target=self._plot, args=(), daemon=True)
        logger.debug("plotting process initialised")
        self.process.start()
        logger.debug("plotter process started")

    def close_plot(self):
        self.process.kill()

    def create_buttons_widget(self):

        # create dock for the buttons widget to live in
        self.button_dock = Dock("Lab notebook", size=(10, 10), closable=True)
        self.area.addDock(self.button_dock, 'right')

        # start with crosshairs off
        self.crosshairs_on = 0

        # widget for buttons to live in
        self.buttons_widget = pg.LayoutWidget()

        # create the buttons/gui elements
        # self.save_layout = QtGui.QPushButton('save dock state')
        # self.restore_layout = QtGui.QPushButton('restore dock state')

        self.crosshairs_button = QtGui.QPushButton('turn on crosshairs')
        self.corner_button = QtGui.QPushButton('corner detection')

        self.text_for_saving = QtGui.QTextEdit("id: {}".format(self.folder.stem))
        self.save_to_notebook_button = QtGui.QPushButton('save to lab notebook')
        self.saved_indicator = QtGui.QLabel('not saved')
        self.file_title = QtGui.QLineEdit('saved file title')

        # grey out restore (will be enabled once the save button has been clicked)
        # self.restore_layout.setEnabled(False)

        # position the gui elements
        self.buttons_widget.addWidget(self.file_title, row=0, col=0)
        self.buttons_widget.addWidget(self.saved_indicator, row=1, col=0)
        self.buttons_widget.addWidget(self.save_to_notebook_button, row=2, col=0)
        self.buttons_widget.addWidget(self.text_for_saving, row=3, col=0)
        self.buttons_widget.addWidget(self.crosshairs_button, row=4, col=0)

        self.button_dock.addWidget(self.buttons_widget)

        # link the buttons to the functions
        self.save_to_notebook_button.clicked.connect(self.save_interesting_file)
        self.crosshairs_button.clicked.connect(self.toggle_crosshairs)

    def toggle_crosshairs(self):
        # toggler (crosshairs on is either 0 or 1)
        self.crosshairs_on += 1
        self.crosshairs_on %= 2

        if self.crosshairs_on:
            self.crosshairs()
            self.crosshairs_button.setText('turn off crosshairs')
        else:
            self.remove_crosshairs()
            self.crosshairs_button.setText('turn on crosshairs')

    def _plot(self):
        # plotting function dictionary to select right function for plotting
        # images or line plots
        length_plot_mapping = {2: self._create_1d_plot, 3: self._create_2d_plot}

        # open the qtgraph window
        self.app = QtGui.QApplication(["qgor {}".format(self.folder.stem)])
        self.win = QtGui.QMainWindow()

        icon_path = str(Path(__file__).parent / self.options.get("icon"))
        icon = QIcon(icon_path)
        self.win.setWindowIcon(icon)

        self.area = DockArea()
        self.win.setCentralWidget(self.area)

        # for saving a png of the image. Needs to be above the creation of the buttons
        directory = self.folder.parent / "pngs"
        self.image_filename = "{}.png".format(str(directory / self.folder.stem))

        pg.setConfigOptions(
            background=self.options.get("background", "k"),
            foreground=self.options.get("foreground", "d"),
        )

        # setting the window size
        window_size = self.options.get("window_size")
        self.win.resize(*window_size)
        self.win.setWindowTitle("{}".format(self.folder.stem))

        # list for keeping track of widgets so they can be updated
        self.widgets = []

        for plot_axis in self.axis:
            # duplicates in plotter cause bugs so make sure this isn't the case. Sometimes it is needed if you want to
            # monitor the value of a set parameter, in which case you must wrap the measured parameter with a class that has
            # a .get() method that calls the other parameter's .get()
            duplicate_assertion_string = (
                "duplicate name in plotted/measured parameters. If you need to monitor a set "
                "parameter please wrap one of the duplicate parameters."
            )

            assert (
                    set(plot_axis).__len__() == plot_axis.__len__()
            ), duplicate_assertion_string

            # select the plot function based on the length of the data
            plot_function = length_plot_mapping.get(plot_axis.__len__())
            plot_function.__call__(*plot_axis)

        self.create_buttons_widget()
        self.win.show()

        self._register_update()
        if (sys.flags.interactive != 1) or not hasattr(QtCore, "PYQT_VERSION"):
            QtGui.QApplication.instance().exec_()

        # self.save_png()




    def _create_1d_plot(self, x, y):

        # get data
        x_mm = self.mm_r.__getattribute__(x)
        y_mm = self.mm_r.__getattribute__(y)



        assert x_mm.size == y_mm.size, "x_mm.size != y_mm.size -- {} != {}".format(
            x_mm.size, y_mm.size
        )

        axis = {
            "x": {"name": x, "unit": self.mm_r.units.get(x)},
            "y": {"name": y, "unit": self.mm_r.units.get(y)},
        }

        # create the plot and dock it lives in
        plot_1d_options = self.options.get("plot_1d_options")
        widget = Plot_1D_Widget(x_mm=x_mm, y_mm=y_mm, axis=axis, **plot_1d_options)
        self.widgets.append(widget)

        # add the dock and plot to the window area
        self.area.addDock(widget.dock)


    def _update(self):
        for widget in self.widgets:
            widget.update()

    def _register_update(self):
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self._update)

        update_time = self.options.get("update_time")
        self.timer.start(update_time)  # how often the self.update is called [ms]

