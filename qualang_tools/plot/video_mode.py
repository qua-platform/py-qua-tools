import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import numpy as np
import plotly.graph_objects as go
import xarray as xr
import time
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)


# VoltageParameter Class remains unchanged
class VoltageParameter:
    def __init__(self, name, initial_value=0.0, units="V"):
        self.name = name
        self.latest_value = initial_value
        self._value = initial_value
        self.units = units
        logging.debug(f"{self.name} initialized with value {self.latest_value} {self.units}")

    def get(self):
        time.sleep(0.2)  # Simulate a 200ms delay
        self.latest_value = self._value
        logging.debug(f"Getting {self.name}: {self.latest_value} {self.units}")
        return self.latest_value

    def set(self, new_value):
        self._value = new_value
        updated_value = self.get()  # Return the value after setting
        logging.debug(f"Setting {self.name} to {new_value}: Actual value is {updated_value} {self.units}")
        return updated_value


# DataGenerator Class remains unchanged
class DataGenerator:
    def __init__(
        self, x_offset_parameter, y_offset_parameter, x_span, y_span, num_averages=1, x_points=101, y_points=101
    ):
        self.x_offset_parameter = x_offset_parameter
        self.y_offset_parameter = y_offset_parameter
        self.x_span = x_span
        self.y_span = y_span
        self.num_averages = num_averages
        self.x_points = x_points
        self.y_points = y_points
        self.data_history = []

        logging.debug("Initializing DataGenerator")

        self.xarr = xr.DataArray(
            self.acquire_data(),
            coords=[("y", self.y_vals), ("x", self.x_vals)],
            attrs={"units": "K", "long_name": "Temperature"},
        )
        self.xarr.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.xarr.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
        logging.debug("DataGenerator initialized with initial data")

    @property
    def x_vals(self):
        x_offset = self.x_offset_parameter.latest_value
        x_min = x_offset - self.x_span / 2
        x_max = x_offset + self.x_span / 2
        return np.linspace(x_min, x_max, self.x_points)

    @property
    def y_vals(self):
        y_offset = self.y_offset_parameter.latest_value
        y_min = y_offset - self.y_span / 2
        y_max = y_offset + self.y_span / 2
        return np.linspace(y_min, y_max, self.y_points)

    def update_voltage_ranges(self):
        self.xarr = self.xarr.assign_coords(x=self.x_vals, y=self.y_vals)

        x_vals = self.x_vals
        y_vals = self.y_vals
        logging.debug(
            f"Updated voltage ranges: "
            f"x_vals=[{x_vals[0]}, {x_vals[1]}, ..., {x_vals[-1]}], "
            f"y_vals=[{y_vals[0]}, {y_vals[1]}, ..., {y_vals[-1]}]"
        )

    def acquire_data(self):
        return np.random.rand(len(self.y_vals), len(self.x_vals))

    def update_data(self):
        new_data = self.acquire_data()

        if new_data.shape != self.xarr.values.shape:
            self.data_history.clear()

        self.data_history.append(new_data)
        logging.debug(f"New data generated with shape: {new_data.shape}")

        if len(self.data_history) > self.num_averages:
            self.data_history.pop(0)

        averaged_data = np.mean(self.data_history, axis=0)

        self.xarr = xr.DataArray(
            averaged_data,
            coords=[("y", self.y_vals), ("x", self.x_vals)],
            attrs=self.xarr.attrs,  # Preserve original attributes like units
        )

        self.xarr.coords["x"].attrs.update({"units": "V", "long_name": self.x_offset_parameter.name})
        self.xarr.coords["y"].attrs.update({"units": "V", "long_name": self.y_offset_parameter.name})
        logging.debug(f"Averaged data calculated with shape: {self.xarr.shape}")
        return self.xarr


# Create Plotly figure function remains unchanged
def create_plotly_figure_from_xarray(da: xr.DataArray):
    x_label = da.coords["x"].attrs.get("long_name", "x")
    x_unit = da.coords["x"].attrs.get("units", "")
    y_label = da.coords["y"].attrs.get("long_name", "y")
    y_unit = da.coords["y"].attrs.get("units", "")
    z_label = da.attrs.get("long_name", da.name or "Value")
    z_unit = da.attrs.get("units", "")

    xaxis_label = f"{x_label} ({x_unit})" if x_unit else x_label
    yaxis_label = f"{y_label} ({y_unit})" if y_unit else y_label
    zaxis_label = f"{z_label} ({z_unit})" if z_unit else z_label

    fig = go.Figure(
        go.Heatmap(
            z=da.values,
            x=da.coords["x"].values,
            y=da.coords["y"].values,
            colorscale="plasma",
            colorbar=dict(title=zaxis_label),
        )
    )
    fig.update_layout(xaxis_title=xaxis_label, yaxis_title=yaxis_label)
    logging.debug("Created Plotly figure from xarray DataArray")
    return fig


# Updated LivePlotter Class
class LivePlotter:
    def __init__(self, data_generator, integration_time=10e-6):
        self.data_generator = data_generator
        self.integration_time = integration_time
        self.paused = False
        self.iteration = 0

        self.app = dash.Dash(__name__)
        self.create_layout()

    def create_layout(self):
        self.fig = create_plotly_figure_from_xarray(self.data_generator.xarr)

        # Modify the layout with CSS to left-align and adjust input size
        self.app.layout = html.Div(
            [
                html.Div(
                    [
                        html.Button(
                            "Pause",
                            id="pause-button",
                            n_clicks=0,
                            style={"width": "20%", "margin-bottom": "10px"},
                        ),
                        html.Div(id="iteration-output", children="Iteration: 0", style={"margin-bottom": "20px"}),
                        html.Div(
                            [
                                html.Label("Integration Time (µs)", style={"text-align": "left", "width": "50%"}),
                                dcc.Input(
                                    id="integration-time",
                                    type="number",
                                    value=self.integration_time * 1e6,
                                    min=1,
                                    debounce=True,
                                    style={"width": "50%"},
                                ),  # Integration time in microseconds
                            ],
                            style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Label("Averages", style={"text-align": "left", "width": "50%"}),
                                dcc.Input(
                                    id="num-averages",
                                    type="number",
                                    value=self.integration_time * 1e6,
                                    min=1,
                                    step=1,
                                    debounce=True,
                                    style={"width": "50%"},
                                ),  # Integration time in microseconds
                            ],
                            style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("X Span (V)", style={"text-align": "left", "width": "50%"}),
                                        dcc.Input(
                                            id="x-span",
                                            type="number",
                                            value=self.data_generator.x_span,
                                            min=0.01,
                                            max=self.data_generator.x_span * 2,
                                            debounce=True,
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Y Span (V)", style={"text-align": "left", "width": "50%"}),
                                        dcc.Input(
                                            id="y-span",
                                            type="number",
                                            value=self.data_generator.y_span,
                                            min=0.01,
                                            max=self.data_generator.y_span * 2,
                                            debounce=True,
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                                ),
                            ],
                            style={"display": "flex", "flex-direction": "column"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("X Points", style={"text-align": "left", "width": "50%"}),
                                        dcc.Input(
                                            id="x-points",
                                            type="number",
                                            value=self.data_generator.x_points,
                                            min=1,
                                            max=501,
                                            step=1,
                                            debounce=True,
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Y Points", style={"text-align": "left", "width": "50%"}),
                                        dcc.Input(
                                            id="y-points",
                                            type="number",
                                            value=self.data_generator.y_points,
                                            min=1,
                                            max=501,
                                            step=1,
                                            debounce=True,
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                                ),
                            ],
                            style={"display": "flex", "flex-direction": "column"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Label("X Offset (V)", style={"text-align": "left", "width": "50%"}),
                                        dcc.Input(
                                            id="x-offset",
                                            type="number",
                                            value=self.data_generator.x_offset_parameter.get(),
                                            debounce=True,
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                                ),
                                html.Div(
                                    [
                                        html.Label("Y Offset (V)", style={"text-align": "left", "width": "50%"}),
                                        dcc.Input(
                                            id="y-offset",
                                            type="number",
                                            value=self.data_generator.y_offset_parameter.get(),
                                            debounce=True,
                                            style={"width": "50%"},
                                        ),
                                    ],
                                    style={"display": "flex", "width": "100%", "margin-bottom": "10px"},
                                ),
                            ],
                            style={"display": "flex", "flex-direction": "column"},
                        ),
                    ],
                    style={"width": "30%", "margin": "auto"},
                ),
                dcc.Graph(id="live-heatmap", figure=self.fig, style={"width": "65%", "height": "100%"}),
                dcc.Interval(id="interval-component", interval=self.update_interval, n_intervals=0),
            ],
            style={"display": "flex", "flex-direction": "row", "height": "100%"},
        )
        logging.debug("Dash layout created")
        self.add_callbacks()

    def clear_data(self):
        """Clears data history and resets averages."""
        self.data_generator.data_history.clear()
        logging.debug("Cleared all averages and data history.")

    @property
    def update_interval(self):
        return self.integration_time * self.data_generator.x_points * self.data_generator.y_points * 1000

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
                Output("interval-component", "interval"),
            ],
            [
                Input("interval-component", "n_intervals"),
                Input("integration-time", "value"),
                Input("num-averages", "value"),
                Input("x-span", "value"),
                Input("y-span", "value"),
                Input("x-points", "value"),
                Input("y-points", "value"),
                Input("x-offset", "value"),
                Input("y-offset", "value"),
            ],
        )
        def update_heatmap(
            n_intervals, integration_time, num_averages, x_span, y_span, x_points, y_points, x_offset, y_offset
        ):
            if self.paused:
                logging.debug(f"Updates paused at iteration {self.iteration}")
                return self.fig, f"Iteration: {self.iteration}", self.update_interval

            attrs = [
                {"obj": self, "attr": "integration_time", "new": integration_time / 1e6},
                {"obj": self.data_generator, "attr": "num_averages", "new": num_averages},
                {"obj": self.data_generator, "attr": "x_span", "new": x_span},
                {"obj": self.data_generator, "attr": "y_span", "new": y_span},
                {"obj": self.data_generator, "attr": "x_points", "new": x_points},
                {"obj": self.data_generator, "attr": "y_points", "new": y_points},
                {"obj": self.data_generator.x_offset_parameter, "attr": "latest_value", "new": x_offset},
                {"obj": self.data_generator.y_offset_parameter, "attr": "latest_value", "new": y_offset},
            ]

            logging.debug(f"***Updating heatmap at iteration {n_intervals}")
            for attr in attrs:
                attr["old"] = getattr(attr["obj"], attr["attr"])

                logging.debug(f"Updating {attr['attr']} from {attr['old']} to {attr['new']}")
                if attr["old"] == attr["new"]:
                    continue

                self.clear_data()

                if attr["attr"] in ["x_offset", "y_offset"]:
                    attr["obj"].set(attr["new"])
                else:
                    setattr(attr["obj"], attr["attr"], attr["new"])

            updated_xarr = self.data_generator.update_data()
            self.fig = create_plotly_figure_from_xarray(updated_xarr)

            # Increment iteration counter and update frontend
            self.iteration += 1
            return self.fig, f"Iteration: {self.iteration}", self.update_interval

    def run(self):
        logging.debug("Starting Dash server")
        self.app.run_server(debug=True)


if __name__ == "__main__":
    x_offset = VoltageParameter(name="X Voltage Offset", initial_value=0.0)
    y_offset = VoltageParameter(name="Y Voltage Offset", initial_value=0.0)
    x_span = 0.1
    y_span = 0.1

    data_generator = DataGenerator(
        x_offset_parameter=x_offset,
        y_offset_parameter=y_offset,
        x_span=x_span,
        y_span=y_span,
        num_averages=5,
        x_points=101,
        y_points=101,
    )

    live_plotter = LivePlotter(data_generator=data_generator, integration_time=10e-6)
    live_plotter.run()
