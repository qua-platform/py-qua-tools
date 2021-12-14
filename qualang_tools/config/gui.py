#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash import Input, Output, html
import os
from .server.app import app
from .server.editors import *
from .server.upload import *
from .server.download import *
import webbrowser

@app.callback(Output("page-content", "children"),
    [Input("url", "pathname")])
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
                dbc.NavLink([html.I(className="bi bi-upload me-2"),
                    "Upload or Start new"], href="/", active="exact"),
                dbc.NavLink([html.I(className="bi bi-sliders me-2"),
                    "View & Edit "], href="/config", active="exact"),
                dbc.NavLink([html.I(className="bi bi-download me-2"),
                    "Download final"]
                , href="/download", active="exact"),
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

app.layout = html.Div([dcc.Location(id="url"),sidebar,content])
guiserver = app.server

if __name__ == '__main__':

    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)

    webbrowser.open("http://localhost:8050")
    app.run_server(host='127.0.0.1', debug=False)
    # alternative when not debugging
    # poetry run gunicorn gui:guiserver -b :8050