from datetime import datetime
from pathlib import Path
from typing import Optional, Union
from dash import dcc, html  # , Input, Output
from dash_extensions.enrich import DashProxy, Output, Input, BlockingCallbackTransform
import dash_bootstrap_components as dbc  # Add this import

import logging

from qualang_tools.control_panel.video_mode.data_acquirers import BaseDataAcquirer
from .dash_tools import create_axis_layout, create_input_field, xarray_to_plotly


__all__ = ["VideoMode"]


class VideoMode:
    """
    A class for visualizing and controlling data acquisition in video mode.

    This class provides a dashboard interface for visualizing and controlling data acquisition in video mode.
    It uses Dash for the web interface and Plotly for the heatmap visualization.

    Attributes:
        data_acquirer (BaseDataAcquirer): The data acquirer object that provides the data to be visualized.
        save_path (Union[str, Path]): The path where data and images will be saved.
        update_interval (float): The interval at which the data is updated in the dashboard (in seconds).
            If the previous update was not finished in the given interval, the update will be skipped.
    """

    def __init__(
        self,
        data_acquirer: BaseDataAcquirer,
        save_path: Union[str, Path] = "./video_mode_output",
        update_interval: float = 0.1,
    ):
        self.data_acquirer = data_acquirer
        self.save_path = Path(save_path)
        self.paused = False
        self._last_update_clicks = 0
        self._last_save_clicks = 0
        self.update_interval = update_interval

        self.app = DashProxy(
            __name__,
            title="Video Mode",
            transforms=[BlockingCallbackTransform(timeout=10)],
            external_stylesheets=[dbc.themes.BOOTSTRAP],
        )  # Add Bootstrap theme
        self.create_layout()

    def create_layout(self):
        """
        Create the layout for the video mode dashboard.

        This method sets up the Dash layout for the video mode control panel. It includes:
        - A graph to display the heatmap of acquired data
        - Controls for X and Y parameters (offset, span, points)
        - Buttons for pausing/resuming data acquisition and saving data
        - Display for the current iteration count
        - Input for setting the number of averages

        The layout is designed to be responsive and user-friendly, with aligned input fields
        and clear labeling. It uses a combination of Dash core components and HTML elements
        to create an intuitive interface for controlling and visualizing the data acquisition
        process.

        Returns:
            None: The method sets up the `self.app.layout` attribute but doesn't return anything.
        """
        self.fig = xarray_to_plotly(self.data_acquirer.data_array)

        self.app.layout = dbc.Container(
            [
                dbc.Row(
                    [
                        dbc.Col(  # Settings
                            [
                                html.H1("Video mode", className="mb-4"),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Pause",
                                                id="pause-button",
                                                n_clicks=0,
                                                className="mb-3",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            html.Div(
                                                id="iteration-output",
                                                children="Iteration: 0",
                                                className="mb-3 ml-3 d-flex align-items-center",
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                    className="mb-4",
                                ),
                                create_input_field(
                                    "num-averages",
                                    "Averages",
                                    self.data_acquirer.num_averages,
                                    min=1,
                                    step=1,
                                    debounce=True,
                                ),
                                html.Div(self.data_acquirer.get_all_dash_components()),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                "Update",
                                                id="update-button",
                                                n_clicks=0,
                                                className="mt-3 mr-2",
                                            ),
                                            width="auto",
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                "Save",
                                                id="save-button",
                                                n_clicks=0,
                                                className="mt-3",
                                            ),
                                            width="auto",
                                        ),
                                    ],
                                ),
                            ],
                            width=5,
                        ),
                        dbc.Col(
                            dcc.Graph(
                                id="live-heatmap",
                                figure=self.fig,
                                style={"height": "100%", "min-width": "500px"},
                            ),
                            width=7,
                        ),
                    ]
                ),
                dcc.Interval(id="interval-component", interval=self.update_interval * 1000, n_intervals=0),
            ],
            fluid=True,
            style={"height": "100vh"},
        )
        logging.debug(f"Dash layout created, update interval: {self.update_interval*1000} ms")
        self.add_callbacks()

    def clear_data(self):
        """Clears data history and resets averages."""
        self.data_acquirer.data_history.clear()
        logging.debug("Cleared all averages and data history.")

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
                Input("num-averages", "value"),
                Input("x-span", "value"),
                Input("y-span", "value"),
                Input("x-points", "value"),
                Input("y-points", "value"),
            ],
            blocking=True,
        )
        def update_heatmap(
            n_intervals,
            n_update_clicks,
            num_averages,
            x_span,
            y_span,
            x_points,
            y_points,
        ):
            logging.debug(f"*** Dash callback {n_intervals} called at {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
            attrs = [
                dict(obj=self.data_acquirer, key="num_averages", new=num_averages),
                dict(obj=self.data_acquirer.x_axis, key="span", new=x_span),
                dict(obj=self.data_acquirer.y_axis, key="span", new=y_span),
                dict(obj=self.data_acquirer.x_axis, key="points", new=x_points),
                dict(obj=self.data_acquirer.y_axis, key="points", new=y_points),
            ]
            updated_attrs = []

            if n_update_clicks > self._last_update_clicks:
                self._last_update_clicks = n_update_clicks
                for attr in attrs:
                    attr["old"] = getattr(attr["obj"], attr["key"])
                    attr["changed"] = attr["old"] != attr["new"]

                    if not attr["changed"]:
                        continue

                    if attr["new"] is None:
                        continue

                    updated_attrs.append(attr)

                    logging.debug(f"Updating {attr['key']} from {attr['old']} to {attr['new']}")

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
            logging.debug(f"Updating heatmap, num_acquisitions: {self.data_acquirer.num_acquisitions}")
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

        # Add callbacks for all dynamic components
        for component in self.data_acquirer.get_all_dash_components():
            if isinstance(component, html.Div):
                for child in component.children:
                    if hasattr(child, "id"):
                        self.create_callback_for_component(child)
            elif hasattr(component, "id"):
                self.create_callback_for_component(component)

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
        data_save_path = self.save_path / "data"
        logging.info(f"Attempting to save data to folder: {data_save_path}")

        if not data_save_path.exists():
            data_save_path.mkdir(parents=True)
            logging.info(f"Created directory: {data_save_path}")

        if idx is None:
            idx = 1
            while idx <= 9999 and (data_save_path / f"data_{idx}.h5").exists():
                idx += 1

        if idx > 9999:
            raise ValueError("Maximum number of data files (9999) reached. Cannot save more.")

        filename = f"data_{idx}.h5"
        filepath = data_save_path / filename

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
        image_save_path = self.save_path / "images"
        logging.info(f"Attempting to save image to folder: {image_save_path}")
        if not image_save_path.exists():
            image_save_path.mkdir(parents=True)
            logging.info(f"Created directory: {image_save_path}")

        idx = 1
        while idx <= 9999 and (image_save_path / f"data_image_{idx}.png").exists():
            idx += 1
        if idx <= 9999:
            filename = f"data_image_{idx}.png"
            filepath = image_save_path / filename
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
        if not self.save_path.exists():
            self.save_path.mkdir(parents=True)
            logging.info(f"Created directory: {self.save_path}")

        # Save image first
        idx = self.save_image()

        # Attempt to save data with the same index
        try:
            self.save_data(idx)
        except FileExistsError:
            logging.warning(f"Data file with index {idx} already exists. Image saved, but data was not overwritten.")

        logging.info(f"Save operation completed with index: {idx}")
        return idx

    def create_callback_for_component(self, component):
        @self.app.callback(Output(component.id, "value"), Input(component.id, "value"))
        def update_attr(value, id=component.id):
            obj, attr = self.data_acquirer.get_object_and_attribute(id)
            setattr(obj, attr, value)
            return value
