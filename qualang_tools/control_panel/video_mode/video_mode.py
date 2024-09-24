import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import logging

from qualang_tools.plot.video_mode.data_acquirers import BaseDataAcquirer
from .plotly_tools import xarray_to_plotly


__all__ = ["VideoMode"]


# Configure logging
logging.basicConfig(level=logging.DEBUG)


class VideoMode:
    def __init__(self, data_acquirer: BaseDataAcquirer):
        self.data_acquirer = data_acquirer

        self.paused = False
        self.iteration = 0

        self.app = dash.Dash(__name__, title="Video Mode")
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
        self.fig = xarray_to_plotly(self.data_acquirer.xarr)

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
                                        ),  # Integration time in microseconds
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
        logging.debug("Dash layout created")
        self.add_callbacks()

    def clear_data(self):
        """Clears data history and resets averages."""
        self.data_acquirer.data_history.clear()
        logging.debug("Cleared all averages and data history.")

    @property
    def update_interval(self):
        return self.data_acquirer.integration_time * self.data_acquirer.x_points * self.data_acquirer.y_points * 1000

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
                Input("live-heatmap", "clickData"),  # This listens to clicks on the graph
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
            n_intervals,
            clickData,
            integration_time,
            num_averages,
            x_span,
            y_span,
            x_points,
            y_points,
            x_offset,
            y_offset,
        ):
            if self.paused:
                logging.debug(f"Updates paused at iteration {self.iteration}")
                return self.fig, f"Iteration: {self.iteration}", self.update_interval

            # Handle click event with Ctrl key pressed
            if clickData:
                import json

                print(json.dumps(clickData, indent=2))
                point = clickData["points"][0]
                x_clicked = point["x"]
                y_clicked = point["y"]
                modifiers = []
                clickData.clear()
                # modifiers = clickData["event"].get("modifiers", [])
                # logging.debug(f"Clicked at ({x_clicked}, {y_clicked}) with modifiers: {modifiers}")

                # Check if 'Control' was held during the click
                if "ctrl" in modifiers:
                    logging.debug(f"Setting x_offset to {x_clicked} and y_offset to {y_clicked}")
                    self.data_acquirer.x_offset_parameter.set(x_clicked)
                    self.data_acquirer.y_offset_parameter.set(y_clicked)
                    self.clear_data()

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

            logging.debug(f"***Updating heatmap at iteration {n_intervals}")
            attrs_modified = False
            for attr in attrs:
                attr["old"] = getattr(attr["obj"], attr["attr"])

                attr["changed"] = attr["old"] != attr["new"]

                if not attr["changed"]:
                    continue

                attrs_modified = True

                logging.debug(f"Updating {attr['attr']} from {attr['old']} to {attr['new']}")

                if attr["attr"] in ["x_offset", "y_offset"]:
                    attr["obj"].set(attr["new"])
                else:
                    setattr(attr["obj"], attr["attr"], attr["new"])
            if attrs_modified:
                self.clear_data()

            updated_xarr = self.data_acquirer.update_data(attrs)
            self.fig = xarray_to_plotly(updated_xarr)

            # Increment iteration counter and update frontend
            self.iteration += 1
            return self.fig, f"Iteration: {self.iteration}", self.update_interval

    def run(self):
        logging.debug("Starting Dash server")
        self.app.run_server(debug=True)
