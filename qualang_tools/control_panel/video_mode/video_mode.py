from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from dash import dcc, html, Input, Output
from dash_extensions.enrich import DashProxy, dcc, html, Output, Input, BlockingCallbackTransform

import logging

from qualang_tools.control_panel.video_mode.data_acquirers import BaseDataAcquirer
from .plotly_tools import xarray_to_plotly


__all__ = ["VideoMode"]


class VideoMode:
    def __init__(
        self,
        data_acquirer: BaseDataAcquirer,
        image_save_path: Union[str, Path] = "./images",
        data_save_path: Union[str, Path] = "./data",
        update_interval: Optional[float] = None,
    ):
        self.data_acquirer = data_acquirer
        self.image_save_path = Path(image_save_path)
        self.data_save_path = Path(data_save_path)
        self.paused = False
        self._last_update_clicks = 0
        self._last_save_clicks = 0
        self._update_interval = update_interval

        self.app = DashProxy(__name__, title="Video Mode", transforms=[BlockingCallbackTransform(timeout=10)])
        self.create_layout()

    def _create_axis_layout(self, axis: str):
        xy = axis.lower()
        XY = axis.upper()
        return html.Div(
            [
                html.Label(XY, style={"text-align": "left"}),
                html.Div(  # span
                    [
                        html.Label(
                            "Span:",
                            style={
                                "text-align": "right",
                                "white-space": "nowrap",
                                "margin-left": "15px",
                                "margin-right": "5px",
                            },
                        ),
                        dcc.Input(
                            id=f"{xy}-span",
                            type="number",
                            value=getattr(self.data_acquirer, f"{xy}_span"),
                            min=0.01,
                            max=getattr(self.data_acquirer, f"{xy}_span") * 2,
                            debounce=True,
                            style={
                                "width": "55px",
                                "text-align": "right",
                            },
                        ),
                        html.Label(
                            "V",
                            style={
                                "text-align": "left",
                                "white-space": "nowrap",
                                "margin-left": "3px",
                            },
                        ),
                    ],
                    style={"display": "flex", "margin-bottom": "10px"},
                ),
                html.Div(  # Points
                    [
                        html.Label(
                            "Points:",
                            style={
                                "text-align": "right",
                                "white-space": "nowrap",
                                "margin-left": "15px",
                                "margin-right": "5px",
                            },
                        ),
                        dcc.Input(
                            id=f"{xy}-points",
                            type="number",
                            value=getattr(self.data_acquirer, f"{xy}_points"),
                            min=1,
                            max=501,
                            step=1,
                            debounce=True,
                            style={
                                "width": "40px",
                                "text-align": "right",
                            },
                        ),
                    ],
                    style={"display": "flex", "margin-bottom": "10px"},
                ),
                html.Div(  # Offset
                    [
                        html.Label(
                            "Offset:",
                            style={
                                "text-align": "right",
                                "white-space": "nowrap",
                                "margin-left": "15px",
                                "margin-right": "5px",
                            },
                        ),
                        dcc.Input(
                            id=f"{xy}-offset",
                            type="number",
                            value=getattr(self.data_acquirer, f"{xy}_offset_parameter").get(),
                            debounce=True,
                            style={
                                "width": "55px",
                                "text-align": "right",
                            },
                        ),
                        html.Label(
                            "V",
                            style={
                                "text-align": "left",
                                "white-space": "nowrap",
                                "margin-left": "3px",
                            },
                        ),
                    ],
                    style={"display": "flex", "margin-bottom": "10px"},
                ),
            ],
            style={"display": "flex", "flex-direction": "row", "flex-wrap": "wrap"},
        )

    def create_layout(self):
        self.fig = xarray_to_plotly(self.data_acquirer.data_array)

        # Modify the layout with CSS to left-align and adjust input size
        self.app.layout = html.Div(
            [
                html.Div(  # Settings
                    [
                        html.Header(
                            "Video mode", style={"font-size": 32, "font-weight": "bold", "margin-bottom": "15px"}
                        ),
                        html.Div(  # Pause + iteration
                            [
                                html.Button(
                                    "Pause",
                                    id="pause-button",
                                    n_clicks=0,
                                    style={"width": "20%", "min-width": "65px"},
                                ),
                                html.Div(
                                    id="iteration-output",
                                    children="Iteration: 0",
                                    style={"margin-left": "15px"},
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flex-direction": "row",
                                "align-items": "center",
                                "margin-bottom": "20px",
                            },
                        ),
                        html.Div(  # Integration + Averages
                            [
                                html.Div(  # Integration
                                    [
                                        html.Label(
                                            "Integration Time:",
                                            style={
                                                "text-align": "right",
                                                "white-space": "nowrap",
                                                "margin-right": "5px",
                                            },
                                        ),
                                        dcc.Input(
                                            id="integration-time",
                                            type="number",
                                            value=self.data_acquirer.integration_time * 1e6,
                                            min=1,
                                            debounce=True,
                                            style={"width": "40px", "text-align": "right"},
                                        ),  # Integration time in microseconds
                                        html.Label(
                                            "µs",
                                            style={
                                                "text-align": "left",
                                                "white-space": "nowrap",
                                                "margin-left": "3px",
                                            },
                                        ),
                                    ],
                                    style={"display": "flex", "margin-bottom": "10px"},
                                ),
                                html.Div(
                                    [
                                        html.Label(
                                            "Averages:",
                                            style={
                                                "text-align": "left",
                                                "white-space": "nowrap",
                                                "margin-left": "15px",
                                                "margin-right": "5px",
                                            },
                                        ),
                                        dcc.Input(
                                            id="num-averages",
                                            type="number",
                                            value=self.data_acquirer.num_averages,
                                            min=1,
                                            step=1,
                                            debounce=True,
                                            style={"width": "40px"},
                                        ),
                                    ],
                                    style={"display": "flex", "margin-bottom": "10px"},
                                ),
                            ],
                            style={
                                "display": "flex",
                                "flex-direction": "row",
                                "flex-wrap": "wrap",
                            },
                        ),
                        self._create_axis_layout("x"),
                        self._create_axis_layout("y"),
                        html.Div(  # Update and Save buttons
                            [
                                html.Button(
                                    "Update",
                                    id="update-button",
                                    n_clicks=0,
                                    style={"margin-top": "20px", "margin-right": "10px"},
                                ),
                                html.Button("Save", id="save-button", n_clicks=0, style={"margin-top": "20px"}),
                            ],
                            style={"display": "flex", "flex-direction": "row"},
                        ),
                    ],
                    style={"width": "40%", "margin": "auto"},
                ),
                dcc.Graph(
                    id="live-heatmap", figure=self.fig, style={"width": "55%", "height": "100%", "min-width": "500px"}
                ),
                dcc.Interval(id="interval-component", interval=self.update_interval, n_intervals=0),
            ],
            style={"display": "flex", "flex-direction": "row", "height": "100%", "flex-wrap": "wrap"},
        )
        logging.debug(f"Dash layout created, update interval: {self.update_interval} ms")
        self.add_callbacks()

    def clear_data(self):
        """Clears data history and resets averages."""
        self.data_acquirer.data_history.clear()
        logging.debug("Cleared all averages and data history.")

    @property
    def update_interval(self):
        if self._update_interval is None:
            return self.data_acquirer.total_measurement_time * 1e3
        return self._update_interval * 1e3

    def add_callbacks(self):
        @self.app.callback(
            Output("pause-button", "children"),
            [Input("pause-button", "n_clicks")],
        )
        def toggle_pause(n_clicks):
            self.paused = not self.paused
            logging.debug(f"Paused: {self.paused}")
            return "Resume" if self.paused else "Pause"

        @self.app.callback(
            [
                Output("live-heatmap", "figure"),
                Output("iteration-output", "children"),
            ],
            [
                Input("interval-component", "n_intervals"),
                Input("update-button", "n_clicks"),
            ],
            [
                Input("integration-time", "value"),
                Input("num-averages", "value"),
                Input("x-span", "value"),
                Input("y-span", "value"),
                Input("x-points", "value"),
                Input("y-points", "value"),
                Input("x-offset", "value"),
                Input("y-offset", "value"),
            ],
            blocking=True,
        )
        def update_heatmap(
            n_intervals,
            n_update_clicks,
            integration_time,
            num_averages,
            x_span,
            y_span,
            x_points,
            y_points,
            x_offset,
            y_offset,
        ):
            logging.debug(f"Dash callback {n_intervals} called at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            attrs = [
                {"obj": self.data_acquirer, "attr": "integration_time", "new": integration_time / 1e6},
                {"obj": self.data_acquirer, "attr": "num_averages", "new": num_averages},
                {"obj": self.data_acquirer, "attr": "x_span", "new": x_span},
                {"obj": self.data_acquirer, "attr": "y_span", "new": y_span},
                {"obj": self.data_acquirer, "attr": "x_points", "new": x_points},
                {"obj": self.data_acquirer, "attr": "y_points", "new": y_points},
                {"obj": self.data_acquirer.x_offset_parameter, "attr": "latest_value", "new": x_offset},
                {"obj": self.data_acquirer.y_offset_parameter, "attr": "latest_value", "new": y_offset},
            ]
            updated_attrs = []

            if n_update_clicks > self._last_update_clicks:
                self._last_update_clicks = n_update_clicks
                for attr in attrs:
                    attr["old"] = getattr(attr["obj"], attr["attr"])

                    attr["changed"] = attr["old"] != attr["new"]

                    if not attr["changed"]:
                        continue

                    updated_attrs.append(attr)

                    logging.debug(f"Updating {attr['attr']} from {attr['old']} to {attr['new']}")

                if updated_attrs:
                    self.clear_data()
                    updated_xarr = self.data_acquirer.update_attrs(updated_attrs)
                return self.fig, f"Iteration: {self.data_acquirer.num_acquisitions}"

            if self.paused:
                logging.debug(f"Updates paused at iteration {self.data_acquirer.num_acquisitions}")
                return self.fig, f"Iteration: {self.data_acquirer.num_acquisitions}"

            # Increment iteration counter and update frontend
            updated_xarr = self.data_acquirer.update_data()
            self.fig = xarray_to_plotly(updated_xarr)
            logging.debug(
                f"***Updating heatmap at iteration {n_intervals}, num_acquisitions: {self.data_acquirer.num_acquisitions}"
            )
            return self.fig, f"Iteration: {self.data_acquirer.num_acquisitions}"

        @self.app.callback(
            Output("save-button", "children"),
            [Input("save-button", "n_clicks")],
        )
        def save(n_clicks):
            if n_clicks > self._last_save_clicks:
                self._last_save_clicks = n_clicks
                self.save()
                return "Saved!"
            return "Save"

    def run(self, debug: bool = True, use_reloader: bool = False):
        logging.debug("Starting Dash server")
        self.app.run_server(debug=debug, use_reloader=use_reloader)

    def save_data(self, idx: Optional[int] = None):
        """
        Save the current data to an HDF5 file.

        This method saves the current data from the data acquirer to an HDF5 file in the specified data save path.
        It automatically generates a unique filename by incrementing an index if not provided.

        Args:
            idx (Optional[int]): The index to use for the filename. If None, an available index is automatically determined.

        Returns:
            int: The index of the saved data file.

        Raises:
            ValueError: If the maximum number of data files (9999) has been reached.
            FileExistsError: If a file with the generated name already exists.

        Note:
            - The data save path is created if it doesn't exist.
            - The filename format is 'data_XXXX.h5', where XXXX is a four-digit index.
        """
        if not self.data_save_path.exists():
            self.data_save_path.mkdir(parents=True)
            logging.info(f"Created directory: {self.data_save_path}")

        if idx is None:
            idx = 1
            while idx <= 9999 and (self.data_save_path / f"data_{idx}.h5").exists():
                idx += 1

        if idx > 9999:
            raise ValueError("Maximum number of data files (9999) reached. Cannot save more.")

        filename = f"data_{idx}.h5"
        filepath = self.data_save_path / filename

        if filepath.exists():
            raise FileExistsError(f"File {filepath} already exists.")
        self.data_acquirer.data_array.to_netcdf(filepath, engine="h5netcdf", format="NETCDF4")
        logging.info(f"Data saved successfully: {filepath}")
        logging.info("Data save operation completed.")
        return idx

    def save_image(self):
        """
        Save the current image to a file.

        This method saves the current figure as a PNG image in the specified image save path.
        It automatically generates a unique filename by incrementing an index.

        Returns:
            int: The index of the saved image file.

        Raises:
            ValueError: If the maximum number of screenshots (9999) has been reached.

        Note:
            - The image save path is created if it doesn't exist.
            - The filename format is 'data_image_XXXX.png', where XXXX is a four-digit index.
        """
        logging.info("Attempting to save image...")
        if not self.image_save_path.exists():
            self.image_save_path.mkdir(parents=True)
            logging.info(f"Created directory: {self.image_save_path}")

        idx = 1
        while idx <= 9999 and (self.image_save_path / f"data_image_{idx}.png").exists():
            idx += 1
        if idx <= 9999:
            filename = f"data_image_{idx}.png"
            filepath = self.image_save_path / filename
            self.fig.write_image(filepath)
            logging.info(f"Image saved successfully: {filepath}")
        else:
            raise ValueError("Maximum number of screenshots (9999) reached. Cannot save more.")
        logging.info("Image save operation completed.")

        return idx

    def save(self):
        """
        Save both the current image and data.

        This method saves the current figure as a PNG image and the current data as an HDF5 file.
        It uses the same index for both files to maintain consistency.

        Returns:
            int: The index of the saved files.

        Raises:
            ValueError: If the maximum number of files (9999) has been reached.

        Note:
            - The image is saved first, followed by the data.
            - If data saving fails due to a FileExistsError, a warning is logged instead of raising an exception.
        """
        logging.info("Attempting to save image and data...")

        # Save image first
        idx = self.save_image()

        # Attempt to save data with the same index
        try:
            self.save_data(idx)
        except FileExistsError:
            logging.warning(f"Data file with index {idx} already exists. Image saved, but data was not overwritten.")

        logging.info(f"Save operation completed with index: {idx}")
        return idx
