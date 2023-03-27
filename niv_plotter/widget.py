"""
Created on 17/09/2021
@author barnaby
"""
import numpy as np
import pyqtgraph as pg
from .Custom_Dock import Dock


class Plot_1D_Widget:
    def __init__(
        self,
        x_mm,
        y_mm,
        axis: dict = {"x": {"name": "x", "unit": ""}, "y": {"name": "y", "unit": ""}},
        line_colour: tuple = (0, 0, 0),
        downsampling_mode: str = "peak",
        clip_to_view: bool = True,
        anti_aliasing: bool = True,
        closeable: bool = False,
        background_colour: str = "black",
        size: tuple = (500, 500),
    ):
        self.x_mm, self.y_mm = x_mm, y_mm

        x_axis = axis.get("x")
        y_axis = axis.get("y")

        # create a dock for the plot to live in
        self.dock = Dock(y_axis.get("name"), size=tuple(size), closable=closeable)
        # the dock can carry the variable name :)
        plot = pg.PlotWidget(title="")

        # setting the axis
        plot.setLabel("bottom", x_axis.get("name", "x"), x_axis.get("unit", ""))
        plot.setLabel("left", y_axis.get("name", "y"), y_axis.get("unit", ""))

        # setting the performance options
        plot.setDownsampling(mode=downsampling_mode)
        plot.setClipToView(clip_to_view)
        plot.setAntialiasing(anti_aliasing)

        # finding the args where nan values don't exist
        args = np.logical_and(
            np.logical_not(np.isnan(x_mm)), np.logical_not(np.isnan(y_mm))
        )

        # drawing the line
        self.line_plot = plot.plot(x_mm[args], y_mm[args], pen=tuple(line_colour))
        self.dock.addWidget(plot)

        self.init_copies()

        self.finished = False

    def init_copies(self):
        self.x = np.full_like(self.x_mm, fill_value=np.nan)
        self.y = np.full_like(self.y_mm, fill_value=np.nan)

    def create_copies(self):
        # creating copies of the memory maps
        self.x = self.x_mm.__array__().copy()
        self.y = self.y_mm.__array__().copy()

    def update(self):

        data_changed = False
        for mm, copy in zip([self.x_mm, self.y_mm], [self.x, self.y]):
            if not np.array_equal(mm, copy):
                data_changed = True

        if data_changed:
            # finding the args where nan values don't exist
            args = np.logical_and(
                np.logical_not(np.isnan(self.x_mm)), np.logical_not(np.isnan(self.y_mm))
            )

            self.line_plot.setData(self.x_mm[args], self.y_mm[args])
            self.create_copies()

        if not self.finished:
            if not np.isnan(np.sum(self.y_mm)):
                self.finished = True