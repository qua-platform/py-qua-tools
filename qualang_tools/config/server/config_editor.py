import importlib
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
import plotly.express as px
import json
import pprint
import numpy as np
import pandas
import html as htmlpy
from .component_editor import editor_of_quantum_machine_elements
from .upload import UPLOAD_DIRECTORY
import os
import urllib.request

__all__ = ["config_editor"]

config_structure = {}

if not os.path.exists(UPLOAD_DIRECTORY):
    os.makedirs(UPLOAD_DIRECTORY)

try:
    # try updating config schema
    print("\tDownloading latest config schema...")
    with urllib.request.urlopen("https://qm-docs.qualang.io/qm_config_spec.json") as url:
        config_structure = json.loads(url.read().decode())
    print("\tDONE")
except Exception:
    print("Cannot download. Using the local copy of the schema.")
    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "qua1_openapi.json")) as file:
        config_structure = json.load(file)


def getDefinition(path):
    key = path.split("/")[2]
    return config_structure["definitions"][key]


def config_editor(pathname, updated_value=None, configuration=None):
    location = pathname.split("/")[2:]

    if configuration is None:
        import config_edits
        import config_final

        importlib.reload(config_edits)
        importlib.reload(config_final)
        configuration = config_final.configuration

    a = configuration

    breadcrumb_items = [{"label": "Config", "href": "/config", "external_link": True}]
    url = "/config"
    selected = ""
    documentation = config_structure["definitions"]["QmConfig"]["properties"]
    waveform_view = False
    pulse_view = False
    controlArguments = ""

    # dive into requested location in the config
    for l in location:
        if (l == "waveforms") and (len(location) > 1 and location[0] != "waveforms"):
            waveform_view = True
        if l == "operations":
            pulse_view = True
        if l != "":
            if l[0] == "[":
                controlArguments = l
                break

            try:
                l = int(l)
            except ValueError:
                pass
            # print(l)
            # print(a)

            if isinstance(a[l], dict) or (isinstance(a[l], list) and len(a[l]) > 0 and isinstance(a[l][0], dict)):
                a = a[l]
                if l in documentation:
                    documentation = documentation[l]
                else:
                    if "properties" in documentation and l in documentation["properties"]:
                        documentation = documentation["properties"][l]
                        if "$ref" in documentation:
                            documentation = getDefinition(documentation["$ref"])
                    elif "additionalProperties" in documentation:
                        if "$ref" in documentation["additionalProperties"]:
                            documentation = getDefinition(documentation["additionalProperties"]["$ref"])
                            # print(documentation)
                        elif "oneOf" in documentation["additionalProperties"]:
                            for option in documentation["additionalProperties"]["oneOf"]:
                                # print("\n")
                                option = getDefinition(option["$ref"])
                                try:
                                    # print(option)
                                    # print(a["type"])
                                    if option["properties"]["type"]["description"].find(a["type"]) != -1:
                                        documentation = option
                                except KeyError:
                                    pass

                    else:
                        documentation = {}
                url += "/" + str(l)
                breadcrumb_items.append(
                    {
                        "label": l,
                        "href": url,
                        "external_link": True,
                    }
                )
            elif pulse_view and (isinstance(a[l], str)):
                pulse_view = False
                selected_pulse = a[l]
                a = configuration["pulses"][selected_pulse]
                url += "/" + l
                breadcrumb_items.append(
                    {
                        "label": ("%s -> %s" % (l, selected_pulse)),
                        "href": url,
                        "external_link": True,
                    }
                )
            else:
                selected = l

    breadcrumb_items[-1]["active"] = True
    input_dict = a

    # print("selected ",selected)
    # print(input_dict)
    # print(controlArguments)

    list_items = []
    for key, value in input_dict.items():
        val = " = "
        className = "text-white"
        if key != selected:
            className = "text-muted"
            if isinstance(value, str):
                val = f" = '{value}'"
            elif isinstance(value, float):
                val = f" = {value}"
            elif isinstance(value, int):
                val = f" = {value}"
            else:
                val = " ..."
        list_items.append(
            dbc.ListGroupItem(
                html.Div(
                    [
                        html.H5(str(key), className="mb-1"),
                        html.Small(
                            val,
                            className=className,
                        ),
                    ],
                    className="d-flex w-100 justify-content-between",
                ),
                href=url + "/" + str(key),
                action=True,
                active=key == selected,
            )
        )
    list_group = dbc.ListGroup(list_items)
    details = []
    docs = []
    # print(documentation)

    # collect relevant documentation
    if "description" in documentation:
        if "title" in documentation:
            docs.append(
                html.H4(
                    "%s: %s" % (breadcrumb_items[-1]["label"], documentation["title"]),
                    className="mb-1",
                )
            )
        docs.append(html.Div(documentation["description"]))
        if "properties" in documentation:
            list_items = []
            for key, value in documentation["properties"].items():
                item = []
                item.append(html.Strong("%s" % key))
                if "$ref" in value:
                    # print(value)
                    value = getDefinition(value["$ref"])
                    # print(value)
                if "type" in value:
                    item.append(html.Span(" (%s)" % value["type"]))
                if "default" in value:
                    item.append(html.Span(", default '%s'" % value["default"]))
                if "description" in value:
                    item.append(html.Span(": %s" % value["description"]))
                list_items.append(dbc.ListGroupItem(item))
            docs.append(dbc.ListGroup(list_items))

    # show selected values
    if selected != "":
        if isinstance(input_dict[selected], list) or isinstance(input_dict[selected], np.ndarray):
            if isinstance(input_dict[selected], np.ndarray):
                input_dict[selected] = input_dict[selected].tolist()

            # print(url)
            if updated_value is not None:
                updated_value = updated_value.replace("[", "")
                updated_value = updated_value.replace("]", "")
                input_dict[selected] = np.fromstring(updated_value, sep=",")
                return "OK"
            if controlArguments.find("view=list") != -1:

                details.append(dcc.Link("view as plot", href=url + f"/{selected}/[view=plot]"))
                # show list
                details.append(
                    dbc.InputGroup(
                        [
                            dbc.Textarea(
                                id="input-field",
                                className="mb-3",
                                placeholder="array",
                                value=htmlpy.escape(pprint.pformat(input_dict[selected])),
                            ),
                            dbc.Button("Update", id="update-button", n_clicks=0),
                        ]
                    )
                )
                details.append(html.Div(id="update-success"))
            else:
                details.append(dcc.Link("view as list", href=url + f"/{selected}/[view=list]"))
                # show plot
                data = pandas.DataFrame(input_dict[selected])
                fig = px.line(data, markers=True)
                fig.update_layout(showlegend=False)
                details.append(dcc.Graph(id="graph", config={"displayModeBar": False}, figure=fig))
        else:
            if isinstance(input_dict[selected], float):
                if updated_value is not None:
                    # do checks
                    input_dict[selected] = updated_value
                    return "OK"
                # else show edit thing
                details.append(
                    dbc.InputGroup(
                        [
                            dbc.Input(
                                id="input-field",
                                placeholder="Enter value...",
                                type="number",
                                value=("%.8e" % input_dict[selected]),
                            ),
                            dbc.Button("Update", id="update-button", n_clicks=0),
                        ]
                    )
                )
                details.append(html.Div(id="update-success"))
            else:
                if waveform_view and isinstance(input_dict[selected], str):
                    options = []
                    for wfoption in configuration["waveforms"].keys():
                        options.append({"label": f"{wfoption}", "value": f"{wfoption}"})
                    details.append(
                        dcc.Dropdown(
                            id="wf-dropdown",
                            options=options,
                            searchable=True,
                            value=input_dict[selected],
                            clearable=False,
                        )
                    )
                    details.append(html.Span(input_dict[selected], id="wf-initial", hidden=True))
                    if updated_value is not None:
                        input_dict[selected] = updated_value
                        return "OK"
                    wf = configuration["waveforms"][input_dict[selected]]
                    if wf["type"] == "arbitrary" or wf["type"] == "compressed":
                        data = pandas.DataFrame(wf["samples"])
                    else:
                        data = pandas.DataFrame([wf["sample"]])
                    fig = px.line(data, markers=True)
                    fig.update_layout(showlegend=False)
                    details.append(dcc.Graph(id="wf-view", config={"displayModeBar": False}, figure=fig))

                    details.append(
                        dcc.Link(
                            "open this waveform",
                            href=("/config/waveforms/%s" % input_dict[selected]),
                            id="wf-link",
                        )
                    )
                else:
                    if isinstance(input_dict[selected], tuple):
                        if updated_value is not None and isinstance(updated_value, tuple):
                            input_dict[selected] = updated_value
                            return "OK"
                        details.append(
                            dbc.InputGroup(
                                [
                                    dbc.InputGroupText("("),
                                    dbc.Input(
                                        id=("tuple-0"),
                                        placeholder="Enter value...",
                                        type="text",
                                        value=("%s" % input_dict[selected][0]),
                                    ),
                                    dbc.InputGroupText(","),
                                    dbc.Input(
                                        id=("tuple-1"),
                                        placeholder="Enter value...",
                                        type="number",
                                        value=("%s" % input_dict[selected][1]),
                                    ),
                                    dbc.InputGroupText(")"),
                                    dbc.Button("Update", id="update-tuple-button", n_clicks=0),
                                ],
                                className="mb-3",
                            )
                        )
                        details.append(details.append(html.Div(id="update-success-tuple")))
                    else:
                        if updated_value is not None:
                            # do checks
                            input_dict[selected] = updated_value
                            return "OK"
                        details.append(
                            dbc.InputGroup(
                                [
                                    dbc.Input(
                                        id="input-field",
                                        placeholder="Enter value...",
                                        type="text",
                                        value=("%s" % input_dict[selected]),
                                    ),
                                    dbc.Button("Update", id="update-button", n_clicks=0),
                                ]
                            )
                        )
                        details.append(html.Div(id="update-success"))

    # add everything to final page
    return html.Div(
        [
            dbc.Breadcrumb(
                items=breadcrumb_items,
            ),
            dbc.Row(
                [
                    dbc.Col(list_group, width=3),
                    dbc.Col(details, width=6),
                    dbc.Col(docs, width=3),
                ]
            ),
            editor_of_quantum_machine_elements(),
        ]
    )
