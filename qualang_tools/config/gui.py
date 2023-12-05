#!/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings

from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash import Input, Output
from .server.app import app
from .server.editors import *
from .server.upload import *
from .server.download import *
from .server import config_editor as ced
import webbrowser
from threading import Timer
import argparse


from waitress import serve


@app.callback(Output("page-content", "children"), [Input("url", "pathname")])
def render_page_content(pathname):
    pathname = str(pathname)

    if pathname == "/":
        return upload
    elif pathname.startswith("/config"):
        return config_editor(pathname)
    elif pathname == "/download":
        return download_page
    # If the user tries to reach a different page, return a 404 message
    return html.H1("404: Not found", className="text-danger")


SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

sidebar = html.Div(
    [
        html.Center(html.H3("ConfigBuilder")),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink(
                    [html.I(className="bi bi-upload me-2"), "Upload or Start new"],
                    href="/",
                    active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-sliders me-2"), "View & Edit "],
                    href="/config",
                    active="exact",
                ),
                dbc.NavLink(
                    [html.I(className="bi bi-download me-2"), "Download final"],
                    href="/download",
                    active="exact",
                ),
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,
)

CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

content = html.Div(id="page-content", style=CONTENT_STYLE)

app.layout = html.Div([dcc.Location(id="url"), sidebar, content])
guiserver = app.server


def open_browser():
    global port_number
    webbrowser.open_new(f"http://localhost:{port_number}")


if __name__ == "__main__":
    warnings.warn(
        "ConfigGUI is no longer being actively developed and may not support all config functionality",
        DeprecationWarning,
        stacklevel=2,
    )
    global port_number

    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--port", help="port number to use for GUI server", type=int)
    args = parser.parse_args()
    if args.port is not None:
        port_number = args.port
    else:
        port_number = 8051
    host = "127.0.0.1"

    timer = Timer(3, open_browser)
    timer.start()
    try:
        print(f"\tConfig GUI is running on http://{host}:{port_number}")
        print("\tIf web browser does not open, please enter the address stated above manually.")
        print("\tStop GUI by pressing Ctrl+C")
        print(
            "\t%s: %s"
            % (
                ced.config_structure["info"]["title"],
                ced.config_structure["info"]["version"],
            )
        )
        serve(app.server, host=host, port=port_number)
        # for development:
        # app.run_server(host="127.0.0.1", debug=False, port=port_number)
    except OSError as e:
        timer.cancel()
        if e.args[0] != 98:
            # if the error is not "address already in use" (trying to bind
            # to a port on which another application is already listening)
            # pass directly the error to the user
            raise e
        print("Port number 8051 is already in use")
        print("Please specify alternative port number as follows:")
        print("python -m qualang_tools.config.gui -p PORT_NUMBER")
