#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from .app import app
import os
from .upload import UPLOAD_DIRECTORY

from dash import Input, Output

__all__ = ["download_page"]


def generate_download_page():
    return html.Div(
        [
            html.P("Please download both files"),
            html.Div(
                [
                    dbc.Button("config_initial.py", id="download-config-inital"),
                    dcc.Download(id="config-initial-data"),
                    html.Span(" + ", style={"fontSize": "3rem", "verticalAlign": "middle"}),
                    dbc.Button("config_edits.py", id="download-config-edits"),
                    dcc.Download(id="config-edits-data"),
                ]
            ),
            html.P("and use it as"),
            html.P(html.Code("from config_edits import configuration, setup")),
            html.P(html.Code("configuration = setup.build(configuration)")),
        ]
    )


download_page = generate_download_page()


@app.callback(
    Output("config-initial-data", "data"),
    Input("download-config-inital", "n_clicks"),
    prevent_initial_call=True,
)
def intial_config_download(n_clicks):
    return dcc.send_file(os.path.join(UPLOAD_DIRECTORY, "config_initial.py"))


@app.callback(
    Output("config-edits-data", "data"),
    Input("download-config-edits", "n_clicks"),
    prevent_initial_call=True,
)
def edit_config_download(n_clicks):
    return dcc.send_file(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"))
