from typing import List

import matplotlib.pyplot as plt

from qualang_tools.wirer.connectivity.wiring_spec import WiringLineType
from qualang_tools.wirer.instruments.instrument_channels import InstrumentChannels
from qualang_tools.wirer.visualizer.instrument_figure_manager import InstrumentFigureManager
from qualang_tools.wirer.visualizer.port_annotation import PortAnnotation


def invert_qubit_dict(qubit_dict) -> dict:
    inverted_dict = {}
    for qubit_ref, element in qubit_dict.items():
        for channel_type, channels in element.channels.items():
            for channel in channels:
                key = (
                    channel.con,
                    channel.slot,
                    channel.port,
                    channel.io_type,
                    channel.signal_type,
                    channel.instrument_id,
                    channel_type,
                )
                if key not in inverted_dict:
                    inverted_dict[key] = []
                annotation = f"{element.id}.{channel_type if isinstance(channel_type, str) else channel_type.value}"
                inverted_dict[key].append((annotation, channel))
    return inverted_dict


def make_annotations(inverted_dict: dict) -> List[PortAnnotation]:
    annotations = []
    for key, values in inverted_dict.items():
        con, slot, port, io_type, signal_type, instrument_id, channel_type = key
        labels = [value[0] for value in values]
        color = get_color_for_line_type(channel_type)
        annotations.append(PortAnnotation(labels, color, con, slot, port, io_type, signal_type, instrument_id))

    return annotations


def make_unused_channel_annotations(available_channels: InstrumentChannels) -> List[PortAnnotation]:
    annotations = []
    for _, channel_list in available_channels.stack.items():
        for channel in channel_list:
            annotations.append(
                PortAnnotation(
                    [""],
                    "white",
                    channel.con,
                    channel.slot,
                    channel.port,
                    channel.io_type,
                    channel.signal_type,
                    channel.instrument_id,
                )
            )

    return annotations


def get_color_for_line_type(line_type) -> str:
    color_map = {
        WiringLineType.FLUX: "powderblue",
        WiringLineType.CHARGE: "lavender",
        WiringLineType.RESONATOR: "peachpuff",
        WiringLineType.DRIVE: "lemonchiffon",
        WiringLineType.COUPLER: "thistle",
    }
    return color_map.get(line_type, "beige")


def draw_annotations(manager: InstrumentFigureManager, annotations: List[PortAnnotation]):
    for annotation in annotations:
        ax = manager.get_ax(annotation.con, annotation.slot, annotation.instrument_id)
        annotation.draw(ax)
        annotation.title_axes(ax)


def visualize(qubit_dict, available_channels=None):
    # Invert the qubit dictionary for easier annotation processing
    inverted_dict = invert_qubit_dict(qubit_dict)

    # Prepare annotations and labels
    annotations = make_annotations(inverted_dict)

    # Manage figures and draw
    manager = InstrumentFigureManager()

    if available_channels is not None:
        available_channel_annotations = make_unused_channel_annotations(available_channels)
        draw_annotations(manager, available_channel_annotations)

    draw_annotations(manager, annotations)

    plt.show()
