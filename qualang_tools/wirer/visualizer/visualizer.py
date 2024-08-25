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
                key = (channel.con, channel.slot, channel.io_type, channel.port, channel.instrument_id, channel_type)
                if key not in inverted_dict:
                    inverted_dict[key] = []
                annotation = f"q{qubit_ref.index if hasattr(qubit_ref, 'index') else f'{qubit_ref.control_index}{qubit_ref.target_index}'}.{channel_type.value}"
                inverted_dict[key].append((annotation, channel))
    return inverted_dict

def prepare_annotations(inverted_dict: dict) -> List[PortAnnotation]:
    annotations = []
    for key, values in inverted_dict.items():
        con, slot, io_type, port, instrument_id, channel_type = key
        labels = [value[0] for value in values]
        color = get_color_for_line_type(channel_type)
        annotations.append(PortAnnotation(labels, color, con, slot, io_type, port, instrument_id))

    return annotations


def prepare_available_channel_annotations(available_channels: InstrumentChannels) -> List[PortAnnotation]:
    annotations = []
    for _, channel_list in available_channels.stack.items():
        for channel in channel_list:
            color = get_color_for_line_type(None)
            annotations.append(PortAnnotation([""], color, channel.con, channel.slot, channel.io_type, channel.port, channel.instrument_id))

    return annotations


def get_color_for_line_type(line_type) -> str:
    color_map = {
        WiringLineType.FLUX: "blue",
        WiringLineType.RESONATOR: "orange",
        WiringLineType.DRIVE: "yellow",
        WiringLineType.COUPLER: "purple"
    }
    return color_map.get(line_type, "white")


def draw_annotations(manager: InstrumentFigureManager, annotations: List[PortAnnotation]):
    for annotation in annotations:
        ax = manager.get_ax(annotation.con, annotation.slot, annotation.instrument_id)
        annotation.draw(ax)
        annotation.title_axes(ax)

def visualize_chassis(qubit_dict, available_channels=None):
    # Invert the qubit dictionary for easier annotation processing
    inverted_dict = invert_qubit_dict(qubit_dict)

    # Prepare annotations and labels
    annotations = prepare_annotations(inverted_dict)

    # Manage figures and draw
    manager = InstrumentFigureManager()

    draw_annotations(manager, annotations)
    if available_channels is not None:
        available_channel_annotations = prepare_available_channel_annotations(available_channels)
        draw_annotations(manager, available_channel_annotations)

    plt.show()
