#!/usr/bin/env python
# -*- coding: utf-8 -*-

import typing
from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from dash import Input, Output
import dash_dangerously_set_inner_html as innerHTML
from docutils.core import publish_doctree, publish_from_doctree
import inspect
import importlib
from .app import app
from .. import primitive_components, components

__all__ = [
    "editor_of_quantum_machine_elements",
    "component_editor",
]


def editor_of_quantum_machine_elements():

    qm_list = []
    component_libraries = ["qualang_tools.config.components"]

    for library in component_libraries:
        for name, obj in inspect.getmembers(importlib.import_module(library)):
            if inspect.isclass(obj) and obj.__module__ == library:
                qm_list.append({"label": f"{name}", "value": f"{library}.{name}"})
    qm_select = dcc.Dropdown(
        id="qm-component-select",
        options=qm_list,
        placeholder="Add new...",
        searchable=True,
        style={"font-size": "1.2rem"},
    )

    return dbc.Row(
        [
            dbc.Col(qm_select, width=3),
            dbc.Col("", id="component-gui", width=6),
            dbc.Col("", id="component-doc", width=3),
        ],
        style={"margin-top": "2rem"},
    )


@app.callback(
    [Output("component-gui", "children"), Output("component-doc", "children")],
    [Input("qm-component-select", "value")],
    prevent_initial_call=True,
)
def get_component_gui(selected_component):
    return component_editor(selected_component)


def component_editor(selected_component, inputs=None):
    if selected_component is None:
        return "", ""

    component, component_class = get_component(selected_component)

    docstring = get_docstring(component_class)

    arugments = inspect.getfullargspec(component_class.__init__)

    argument_names = arugments[0][1:]
    argument_types = arugments[6]
    component_gui = []

    import config_edits

    importlib.reload(config_edits)
    setup = config_edits.setup

    input_index = [0, 0]
    python_command = f"{component_class.__name__}("

    if inputs is None:
        inputs = [None, None]

    python_command, component_gui, input_index = class_editor_and_gui(
        component_class.__init__,
        setup,
        component_gui,
        python_command,
        inputs,
        input_index,
        input_types=["component-input", "port-list"],
    )

    # objects that we can add through add method
    additional_add_docstring = ""
    if hasattr(component_class, "add") and callable(component_class.add) and inputs[0] is None and inputs[1] is None:

        arugments = inspect.getfullargspec(component_class.add)
        argument_names = arugments[0][1:]
        argument_types = arugments[6]

        possible_add_on_objects_gui = []
        add_index = [0, 0]

        for index, name in enumerate(argument_names):

            possible_addons = [
                primitive_components.Operation,
                primitive_components.Weights,
                components.DigitalWaveform,
                components.Mixer,
                primitive_components.IntegrationWeights,
            ]
            for addon in possible_addons:
                # print(index," ",name, " ", argument_types[name])
                gui2 = []
                docs2 = ""
                option_name = ""
                if addon in typing.get_args(argument_types[name]):
                    add_class_name = f"{addon.__module__}.{addon.__qualname__}"
                    gui2.append(html.Small(add_class_name, className="text-muted"))
                    gui2.append(innerHTML.DangerouslySetInnerHTML(docs2))
                    forget, gui2, add_index = class_editor_and_gui(
                        addon,
                        setup,
                        gui2,
                        python_command,
                        inputs,
                        add_index,
                        input_types=[
                            "optional-class-input",
                            "optional-class-port-list",
                        ],
                    )
                    number_of_input_fields = len(gui2) - 2
                    gui2.append(
                        dbc.Input(
                            value=("%d" % number_of_input_fields),
                            id={
                                "type": "optional-class-fieldcount",
                                "index": add_index[0] + 1,
                            },
                            style={"display": "none"},
                        )
                    )
                    gui2.append(
                        dbc.Input(
                            value=(add_class_name),
                            id={
                                "type": "optional-class-name",
                                "index": add_index[0] + 1,
                            },
                            style={"display": "none"},
                        )
                    )
                    gui2.append(
                        dcc.Dropdown(
                            options=[],
                            value=[],
                            multi=True,
                            style={"display": "none"},
                            id={
                                "type": "optional-class-selection",
                                "index": add_index[0] + 1,
                            },
                        )
                    )

                    docs2 = get_docstring(addon)
                    option_name = addon.__name__
                    gui2.append(
                        dbc.Button(
                            "Add option to component",
                            color="secondary",
                            className="me-1",
                            id={"index": add_index[0] + 1, "type": "button-add-option"},
                        )
                    )
                    gui2.append(
                        html.Div(
                            "",
                            id={
                                "type": "optional-class-status",
                                "index": add_index[0] + 1,
                            },
                        )
                    )
                    possible_add_on_objects_gui.append(dbc.AccordionItem(gui2, title=option_name))

        component_gui.append(
            dbc.InputGroup(
                [
                    dbc.InputGroupText([html.I(className="bi bi-stack me-2"), "Add"]),
                    dcc.Dropdown(
                        options=[],
                        value=[],
                        multi=True,
                        placeholder="add optional objects using the menu below",
                        style={"width": "100%"},
                        id="component-input-add",
                    ),
                ],
                className="mb-3",
            )
        )
        if component_class.add.__doc__ is not None:
            additional_add_docstring = "Add: " + component_class.add.__doc__

        component_gui.append(
            dbc.Accordion(
                possible_add_on_objects_gui,
                start_collapsed=True,
            )
        )
    else:
        component_gui.append(
            dcc.Dropdown(
                options=[],
                value=[],
                multi=True,
                placeholder="add optional objects using the menu below",
                style={"display": "none"},
                id="component-input-add",
            )
        )

    if inputs[0] is not None or inputs[1] is not None:
        python_command += ")"
        return python_command

    component_gui.append(
        dbc.Button(
            "Add component",
            color="primary",
            className="me-1",
            id="button-add-component",
        )
    )
    component_gui.append(html.Div("", id="component-status"))
    docs = [
        html.H4(component),
        html.Small(selected_component, className="text-muted"),
        innerHTML.DangerouslySetInnerHTML(docstring),
        innerHTML.DangerouslySetInnerHTML(additional_add_docstring),
    ]

    return component_gui, docs


def one_or_single_type_of(some_type):
    return typing.Union[some_type, typing.List[some_type]]


def class_editor_and_gui(
    selected_class,
    setup,
    component_gui,
    python_command,
    inputs,
    input_index,
    input_types,
):
    arugments = inspect.getfullargspec(selected_class)
    # print(arugments)
    argument_names = arugments[0][1:]
    argument_types = arugments[6]

    for index_arg, name in enumerate(argument_names):
        # print(index_arg," ",name, " ",argument_types[name])
        if argument_types[name] == str:
            if inputs[0] is not None:
                value = inputs[0][input_index[0]].replace("'", "")
                python_command += (",\n  " if (index_arg > 0) else "") + f"'{value}'"
            else:
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name),
                            dbc.Input(
                                placeholder="string",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == float:
            if inputs[0] is not None:
                value = float(inputs[0][input_index[0]])
                python_command += (",\n  " if (input_index[1] > 0 or input_index[0] > 0) else "") + f"{value}"
            else:
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name),
                            dbc.Input(
                                placeholder="float",
                                type="number",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == int:
            if inputs[0] is not None:
                value = int(inputs[0][input_index[0]])
                python_command += (",\n  " if (input_index[1] > 0 or input_index[0] > 0) else "") + f"{value}"
            else:
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name),
                            dbc.Input(
                                placeholder="integer",
                                type="number",
                                step=1,
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == typing.List[float]:
            if inputs[0] is not None:
                python_command += (
                    ",\n  " if (input_index[1] > 0 or input_index[0] > 0) else ""
                ) + f"[{inputs[0][input_index[0]]}]"
            else:
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name),
                            dbc.Textarea(
                                placeholder="float, float, ...",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    ),
                )
            input_index[0] += 1
        elif argument_types[name] == typing.List[primitive_components.DigitalSample]:
            if inputs[0] is not None:
                python_command += (
                    ",\n  " if (input_index[1] > 0 or input_index[0] > 0) else ""
                ) + f"[{inputs[0][input_index[0]]}]"
            else:
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name),
                            dbc.Textarea(
                                placeholder="(0 or 1, duration in ns), (... , ...), ...",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    ),
                )
            input_index[0] += 1
        elif argument_types[name] in [
            primitive_components.AnalogOutputPort,
            primitive_components.AnalogInputPort,
            primitive_components.DigitalOutputPort,
            primitive_components.DigitalInputPort,
        ]:
            controllers = setup.find_instances(components.Controller)
            controllerList = []

            if inputs[0] is not None:
                controller_id = int(inputs[0][input_index[0]])
                port_id = int(inputs[0][input_index[0] + 1])
                command = f"setup.find_instances(Controller)[{controller_id}]"
                if argument_types[name] == primitive_components.AnalogOutputPort:
                    command += f".analog_output({port_id})"
                elif argument_types[name] == primitive_components.AnalogInputPort:
                    command += f".analog_input({port_id})"
                elif argument_types[name] == primitive_components.DigitalOutputPort:
                    command += f".digital_output({port_id})"
                elif argument_types[name] == primitive_components.DigitalInputPort:
                    command += f".digital_input({port_id})"
                python_command += (",\n" if (input_index[0] > 0 or input_index[1] > 0) else "") + command
            else:
                for index, c in enumerate(controllers):
                    controllerList.append({"label": c.name, "value": index})

                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText([html.I(className="bi bi-diagram-3-fill me-2"), name]),
                            dcc.Dropdown(
                                options=controllerList,
                                placeholder="choose controller",
                                style={"min-width": "50%"},
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                            dbc.InputGroupText("port_id"),
                            dbc.Input(
                                placeholder="integer",
                                type="number",
                                step=1,
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0] + 1,
                                },
                            ),
                        ],
                        className="mb-3",
                    ),
                )
            input_index[0] += 2
        elif argument_types[name] in [
            typing.List[primitive_components.AnalogOutputPort],
            typing.List[primitive_components.AnalogInputPort],
            typing.List[primitive_components.DigitalInputPort],
            typing.List[primitive_components.DigitalOutputPort],
        ]:
            controllers = setup.find_instances(components.Controller)
            controllerList = []

            if inputs[0] is not None:
                list = "["

                for index, port in enumerate(inputs[1][input_index[1]]):
                    if index > 0:
                        list += ",\n  "
                    port = port.split(",")
                    controller_id = int(port[0])
                    port_id = int(port[1])
                    if argument_types[name] == typing.List[primitive_components.AnalogOutputPort]:
                        list += f"setup.find_instances(Controller)[{controller_id}].analog_output({port_id})"
                    elif argument_types[name] == typing.List[primitive_components.AnalogInputPort]:
                        list += f"setup.find_instances(Controller)[{controller_id}].analog_input({port_id})"
                    elif argument_types[name] == typing.List[primitive_components.DigitalOutputPort]:
                        list += f"setup.find_instances(Controller)[{controller_id}].digital_output({port_id})"
                    else:
                        # it is (argument_types[name] == typing.List[quantum_machine.primitive_components.DigitalInputPort])
                        list += f"setup.find_instances(Controller)[{controller_id}].digital_input({port_id})"

                list += "]"
                python_command += (",\n  " if (input_index[1] > 0 or input_index[0] > 0) else "") + list
            else:
                for index, c in enumerate(controllers):
                    controllerList.append({"label": c.name, "value": "%s, %d" % (c.name, index)})

                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("List of " + name + ""),
                            dcc.Dropdown(
                                options=[],
                                value=[],
                                multi=True,
                                placeholder="Add to list using form below",
                                style={"width": "100%"},
                                id={
                                    "type": input_types[1],
                                    "index": input_index[1],
                                },
                            ),
                        ]
                    )
                )

                # note: input_index[1] here doesn't change as these fields are not
                # returned from the final form (they are just in subform to help)
                # selection
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name[:-1]),
                            dcc.Dropdown(
                                options=controllerList,
                                placeholder="choose controller",
                                style={"min-width": "30%"},
                                id={
                                    "type": "input-controller",
                                    "index": input_index[1],
                                },
                            ),
                            dbc.InputGroupText("port_id"),
                            dbc.Input(
                                placeholder="integer",
                                type="number",
                                step=1,
                                id={
                                    "type": "input-port",
                                    "index": input_index[1],
                                },
                                style={"min-width": "10%"},
                            ),
                            dbc.Button(
                                "Add to list",
                                id={
                                    "type": "port-button",
                                    "index": input_index[1],
                                },
                            ),
                        ],
                        className="mb-3",
                    ),
                )

            input_index[1] += 1
        elif argument_types[name] == typing.List[primitive_components.Waveform]:
            waveforms = setup.find_instances(primitive_components.Waveform)
            waveformList = []
            if inputs[0] is not None:
                list = "["

                for index, component_index in enumerate(inputs[0][input_index[0]]):
                    if index > 0:
                        list += ",\n  "
                    list += f"setup.find_instances(Waveform)[{component_index}]"

                list += "]"
                python_command += (",\n  " if (input_index[1] > 0 or input_index[0] > 0) else "") + list
            else:
                for index, c in enumerate(waveforms):
                    waveformList.append({"label": c.name, "value": index})

                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("List of " + name + ""),
                            dcc.Dropdown(
                                options=waveformList,
                                value=[],
                                multi=True,
                                placeholder="Click and select available waveforms",
                                style={"width": "100%"},
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == primitive_components.Pulse:
            if inputs[0] is not None:
                python_command += (
                    ",\n" if (input_index[0] > 0 or input_index[1] > 0) else ""
                ) + f"setup.find_instances(Pulse)[{inputs[0][input_index[0]]}]"
            else:
                pulses = setup.find_instances(primitive_components.Pulse)
                pulseList = []
                for index, c in enumerate(pulses):
                    pulseList.append({"label": c.name, "value": index})

                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("List of " + name + ""),
                            dcc.Dropdown(
                                options=pulseList,
                                value=[],
                                multi=False,
                                placeholder="Select available pulse",
                                style={"width": "100%"},
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0] + 1,
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == typing.List[components.Element]:
            elements = setup.find_instances(components.Element)
            elementList = []
            if inputs[0] is not None:
                list = "["

                for index, component_index in enumerate(inputs[0][input_index[0]]):
                    if index > 0:
                        list += ",\n  "
                    list += f"setup.find_instances(Element)[{component_index}]"

                list += "]"
                python_command += (",\n  " if (input_index[1] > 0 or input_index[0] > 0) else "") + list
            else:
                for index, c in enumerate(elements):
                    elementList.append({"label": c.name, "value": index})

                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("List of " + name + ""),
                            dcc.Dropdown(
                                options=elementList,
                                value=[],
                                multi=True,
                                placeholder="Click and select available elements",
                                style={"width": "100%"},
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == primitive_components.IntegrationWeights:
            if inputs[0] is not None:

                selection = inputs[0][input_index[0]].split(",")[0]
                index = inputs[0][input_index[0]].split(",")[1]

                if selection == 1:
                    python_command += (
                        ",\n  " if (input_index[1] > 0 or input_index[0] > 0) else ""
                    ) + f"setup.find_instances(ConstantIntegrationWeights)[{index}]"
                else:
                    # selection == 2
                    python_command += (
                        ",\n  " if (input_index[1] > 0 or input_index[0] > 0) else ""
                    ) + f"setup.find_instances(ArbitraryIntegrationWeights)[{index}]"
            else:
                options1 = setup.find_instances(components.ConstantIntegrationWeights)
                options2 = setup.find_instances(components.ArbitraryIntegrationWeights)
                weights_list = []
                for index, c in enumerate(options1):
                    weights_list.append(
                        {
                            "label": "ConstantIntegrationWeights : " + c.name,
                            "value": f"1,{index}",
                        }
                    )
                for index, c in enumerate(options2):
                    weights_list.append(
                        {
                            "label": "ArbitraryIntegrationWeights : " + c.name,
                            "value": f"2,{index}",
                        }
                    )

                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText("List of " + name + ""),
                            dcc.Dropdown(
                                options=weights_list,
                                value=[],
                                multi=False,
                                placeholder="Select integration weights",
                                style={"width": "100%"},
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                        ],
                        className="mb-3",
                    )
                )
            input_index[0] += 1
        elif argument_types[name] == primitive_components.Matrix2x2:
            if inputs[0] is not None:
                a = float(inputs[0][input_index[0]])
                b = float(inputs[0][input_index[0] + 1])
                c = float(inputs[0][input_index[0] + 2])
                d = float(inputs[0][input_index[0] + 3])
                python_command += (
                    ",\n  " if (input_index[1] > 0 or input_index[0] > 0) else ""
                ) + f"Matrix2x2([[{a},{b}],[{c},{d}]])"
            else:
                component_gui.append(
                    dbc.InputGroup(
                        [
                            dbc.InputGroupText(name + " = [ ["),
                            dbc.Input(
                                placeholder="float",
                                type="number",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0],
                                },
                            ),
                            dbc.InputGroupText(" , "),
                            dbc.Input(
                                placeholder="float",
                                type="number",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0] + 1,
                                },
                            ),
                            dbc.InputGroupText("], ["),
                            dbc.Input(
                                placeholder="float",
                                type="number",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0] + 2,
                                },
                            ),
                            dbc.InputGroupText(" , "),
                            dbc.Input(
                                placeholder="float",
                                type="number",
                                id={
                                    "type": input_types[0],
                                    "index": input_index[0] + 3,
                                },
                            ),
                            dbc.InputGroupText("] ]"),
                        ],
                        className="mb-3",
                    ),
                )
            input_index[0] += 4
        else:
            print("Unknown data type")
            print(argument_types[name])

    return python_command, component_gui, input_index


def get_docstring(selected_class):
    if selected_class.__init__ is not None and selected_class.__init__.__doc__ is not None:
        docstring = publish_doctree(selected_class.__init__.__doc__)
        docstring = publish_from_doctree(docstring, writer_name="html").decode()
    else:
        docstring = ""
    return docstring


def get_component(selected_component):
    component_class = None
    if isinstance(selected_component, str):
        component = selected_component.split(".")[-1]
        library = inspect.getmembers(importlib.import_module(selected_component[0 : -len(component) - 1]))

        for name, obj in library:
            if name == component:
                component_class = obj
    else:
        component_class = selected_component
    return component, component_class
