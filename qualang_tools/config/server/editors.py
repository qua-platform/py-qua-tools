#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dash_bootstrap_components as dbc
from dash import Input, Output, State, MATCH, ALL, ALLSMALLER
from dash.exceptions import PreventUpdate
import pandas
import plotly.express as px
import traceback
import os
import importlib
from .app import app

from .config_editor import config_editor
from .component_editor import component_editor, get_component, class_editor_and_gui
from .upload import UPLOAD_DIRECTORY

__all__ = ["config_editor"]


@app.callback(
    [Output("update-success", "children")],
    [Input("update-button", "n_clicks")],
    [State("input-field", "value"), State("url", "pathname")],
)
def update_field(click_number, value, pathname):
    if isinstance(value, str):
        value = value.replace("\n", " ")
    if click_number == 0:
        return [""]
    success = config_editor(pathname, updated_value=value)
    if success == "OK":
        with open(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"), "a") as myfile:
            if isinstance(value, str):
                myfile.write(f"config_editor('{pathname}', updated_value='{value}', configuration=configuration)\n")
            else:
                myfile.write(f"config_editor('{pathname}', updated_value={value}, configuration=configuration)\n")
        return [dbc.Alert(f"Updated {pathname} = {value}", color="success")]
    else:
        return [dbc.Alert(f"{success}", color="danger")]


@app.callback(
    [Output("update-success-tuple", "children")],
    [Input("update-tuple-button", "n_clicks")],
    [State("tuple-0", "value"), State("tuple-1", "value"), State("url", "pathname")],
    prevent_initial_call=True,
)
def update_tuple(click_number, value0, value1, pathname):
    if click_number == 0:
        return [""]
    success = config_editor(pathname, updated_value=(value0, value1))
    if success == "OK":
        with open(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"), "a") as myfile:
            myfile.write(
                f"config_editor('{pathname}', updated_value=('{value0}',{value1}), configuration=configuration)\n"
            )

        return [dbc.Alert(f"Updated {pathname} = ('{value0}', {value1})", color="success")]
    else:
        return [dbc.Alert(f"{success}", color="danger")]


@app.callback(
    [Output("wf-view", "figure"), Output("wf-link", "href")],
    [Input("wf-dropdown", "value")],
    [State("url", "pathname"), State("wf-initial", "children")],
    prevent_initial_call=True,
)
def update_wf(value, pathname, initial_waveform):
    if value == initial_waveform:
        raise PreventUpdate

    success = config_editor(pathname, updated_value=value)
    if success == "OK":
        with open(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"), "a") as myfile:
            if isinstance(value, str):
                myfile.write(f"config_editor('{pathname}', updated_value='{value}', config=configuration)\n")
            else:
                myfile.write(f"config_editor('{pathname}', updated_value={value}, config=configuration)\n")
        import config_edits
        import config_final

        importlib.reload(config_edits)
        importlib.reload(config_final)
        configuration = config_final.configuration

        wf = configuration["waveforms"][value]
        if wf["type"] == "arbitrary" or wf["type"] == "compressed":
            data = pandas.DataFrame(wf["samples"])
        else:
            data = pandas.DataFrame([wf["sample"]])
        fig = px.line(data, markers=True)
        fig.update_layout(showlegend=False)
        return [fig, f"/config/waveforms/{value}"]
    else:
        print("Error")
        print(success)
        raise PreventUpdate


@app.callback(
    [
        Output({"type": "port-list", "index": MATCH}, "value"),
        Output({"type": "port-list", "index": MATCH}, "options"),
    ],
    [Input({"type": "port-button", "index": MATCH}, "n_clicks")],
    [
        State({"type": "port-list", "index": MATCH}, "options"),
        State({"type": "port-list", "index": MATCH}, "value"),
        State({"type": "input-controller", "index": MATCH}, "value"),
        State({"type": "input-port", "index": MATCH}, "value"),
    ],
    prevent_initial_call=True,
)
def add_port_to_list(bclick, options, values, controller, port):
    if options is None:
        options = []
    if values is None:
        values = []
    controller = controller.split(",")
    controller_name = controller[0]
    controller_index = int(controller[1])
    newController = f"{controller_index}, {port}"
    if newController not in values:
        values.append(newController)
    newOption = {
        "label": f"{controller_name}, {port}",
        "value": f"{controller_index}, {port}",
    }
    if newOption not in options:
        options.append(newOption)
    return values, options


@app.callback(
    Output("component-status", "children"),
    Input("button-add-component", "n_clicks"),
    [
        State({"type": "component-input", "index": ALL}, "value"),
        State({"type": "port-list", "index": ALL}, "value"),
        State("component-input-add", "value"),
        State("qm-component-select", "value"),
    ],
    prevent_initial_call=True,
)
def add_component_click(bclick, inputs, ports, added_objects, selected_component):
    try:
        python_edit_command = component_editor(selected_component, inputs=[inputs, ports])
        if added_objects is not None:
            for index, item in enumerate(added_objects):
                if index == 0:
                    python_edit_command += f".add([{item}"
                else:
                    python_edit_command += f", {item}"
            if len(added_objects) > 0:
                python_edit_command += "])"
        with open(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"), "a") as myfile:
            myfile.write(f"setup.add({python_edit_command})\n")

        return dbc.Alert(f"Component added successfuly!\n {python_edit_command}", color="success")
    except Exception:
        return dbc.Alert(traceback.format_exc(), color="danger")


@app.callback(
    [
        Output({"type": "optional-class-selection", "index": MATCH}, "value"),
        Output({"type": "optional-class-selection", "index": MATCH}, "options"),
        Output({"type": "optional-class-status", "index": MATCH}, "children"),
    ],
    [Input({"type": "button-add-option", "index": MATCH}, "n_clicks")],
    [
        State({"type": "optional-class-fieldcount", "index": MATCH}, "value"),
        State({"type": "optional-class-name", "index": MATCH}, "value"),
        State({"type": "optional-class-selection", "index": MATCH}, "value"),
        State({"type": "optional-class-selection", "index": MATCH}, "options"),
        State({"type": "optional-class-input", "index": ALLSMALLER}, "value"),
    ],
    prevent_intial_call=True,
)
def add_optional_input(
    button_click,
    fieldcount,
    class_name,
    current_added_items,
    current_options,
    class_input,
):
    fieldcount = int(fieldcount)
    from config_edits import setup

    component, component_class = get_component(class_name)

    try:
        python_command, forget, forget = class_editor_and_gui(
            component_class.__init__,
            setup,
            [],
            "",
            [class_input[-fieldcount:], []],
            [0, 0],
            input_types=["component-input", "port-list"],
        )

        python_command = component + "(" + python_command + ")"

        # add on current class list
        current_options.append({"label": python_command, "value": python_command})
        current_added_items.append(python_command)

        return (
            current_added_items,
            current_options,
            dbc.Alert(f"Component added successfuly!\n {python_command}", color="success"),
        )
    except Exception:
        raise PreventUpdate
        # for debugging purposes comment previous line and let this be seen
        return (
            current_added_items,
            current_options,
            dbc.Alert(traceback.format_exc(), color="danger"),
        )


@app.callback(
    [Output("component-input-add", "value"), Output("component-input-add", "options")],
    [Input({"type": "optional-class-selection", "index": ALL}, "value")],
    [State({"type": "optional-class-selection", "index": ALL}, "options")],
    prevent_intial_call=True,
)
def collect_all_added_objects(listed_objects, possible_options):
    all_objects = []
    all_options = []
    for l in listed_objects:
        all_objects += l
    for o in possible_options:
        all_options += o

    return all_objects, all_options
