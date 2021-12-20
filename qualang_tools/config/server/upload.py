#!/usr/bin/env python
# -*- coding: utf-8 -*-

from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from .app import app
import os
import sys
import base64

from dash import Input, Output, State

__all__ = ["upload", "UPLOAD_DIRECTORY"]

UPLOAD_DIRECTORY = os.path.join(os.getcwd(), "config_gui_temp")
sys.path.append(UPLOAD_DIRECTORY)

upload = html.Div(
    [
        html.P(
            [
                "Please upload below your files",
                " or ",
                dbc.Button(
                    "start from empty config",
                    color="primary",
                    className="me-1",
                    id="button-empty-config",
                ),
                html.P(id="config-initial-status"),
            ]
        ),
        dcc.Upload(
            id="upload-config",
            children=html.Div(
                [
                    "Python file that generates global variable ",
                    html.Strong("configuration "),
                    "(Drag and Drop or Click to select)",
                ]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),
        html.Div(id="output-data-upload"),
        dcc.Upload(
            id="upload-config-edits",
            children=html.Div(
                [
                    "Optionally, any previously generated ",
                    html.Strong("config_edits.py"),
                    "(Drag and Drop or Click to select)",
                ]
            ),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=False,
        ),
        html.Div(id="output-data-edits-upload"),
    ]
)


@app.callback(
    [Output("output-data-upload", "children")],
    Input("upload-config", "contents"),
    State("upload-config", "filename"),
    State("upload-config", "last_modified"),
)
def upload_init_config(contents, filename, last_modified):
    if contents is not None:
        init_edits_file()
        init_final_config_file()
        save_file(os.path.join(UPLOAD_DIRECTORY, "config_initial.py"), contents)
        print("OK")
        return [html.P(f"Uploaded {filename}")]
    return [""]


@app.callback(
    [Output("output-data-edits-upload", "children")],
    Input("upload-config-edits", "contents"),
    State("upload-config-edits", "filename"),
    State("upload-config-edits", "last_modified"),
)
def upload_config_edits(contents, filename, last_modified):
    if contents is not None:
        save_file(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"), contents)
        return [html.P(f"Uploaded {filename}")]
    return [""]


def save_file(name, content):
    """Decode and store a file uploaded with Plotly Dash."""
    data = content.encode("utf8").split(b";base64,")[1]
    with open(os.path.join(UPLOAD_DIRECTORY, name), "wb") as fp:
        fp.write(base64.decodebytes(data))


@app.callback(
    Output("config-initial-status", "children"),
    Input("button-empty-config", "n_clicks"),
    prevent_initial_call=True,
)
def enter_empty_config(click):
    init_empty_initial_config_file()
    init_edits_file()
    init_final_config_file()

    return "Starting from empty configuration..."


def init_edits_file():
    with open(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"), "w") as fp:
        fp.write(
            """
from qualang_tools.config import *
from qualang_tools.config.server.config_editor import config_editor
from config_initial import configuration

setup = ConfigBuilder()

"""
        )


def init_empty_initial_config_file():
    with open(os.path.join(UPLOAD_DIRECTORY, "config_initial.py"), "w") as fp:
        fp.write(
            """
configuration = {
    "version": 1,
    "controllers": {},
    "elements": {},
    "pulses": {},
    "waveforms": {},
    "digital_waveforms": {},
    "integration_weights": {},
    "oscillators": {},
    "mixers": {},
}
"""
        )


def init_final_config_file():
    with open(os.path.join(UPLOAD_DIRECTORY, "config_final.py"), "w") as fp:
        fp.write(
            """
from config_edits import configuration, setup

configuration = setup.build(configuration)
"""
        )
