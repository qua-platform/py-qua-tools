import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Define the chassis dimensions
CHASSIS_DIMENSIONS = {
    "OPX1000": {"width": 8, "height": 3},
    "OPX+": {"width": 3, "height": 1},
    "Octave": {"width": 3, "height": 1}
}

# Define the port positions for different modules
PORT_SPACING_FACTOR = 0.1
PORT_POSITIONS = {
    "lf-fem": {
        "output": [(0.25, 1 - i * PORT_SPACING_FACTOR) for i in range(8)],
        "input": [(0.75, 1 - i * PORT_SPACING_FACTOR * 7) for i in range(2)],
    },
    "mw-fem": {
        "output": [(0.25, 1 - i * PORT_SPACING_FACTOR) for i in range(8)],
        "input": [(0.75, 1 - i * PORT_SPACING_FACTOR * 7) for i in range(2)],
    },
    "digital_output": [(0.25 + j * 0.2, 1 - i * PORT_SPACING_FACTOR * 10) for i in range(2) for j in range(5)],
    "analog_output": [(0.25 + j * 0.2, 1 - i * PORT_SPACING_FACTOR * 10) for i in range(2) for j in range(5)],
    "analog_input": [(0.75, 1 - i * PORT_SPACING_FACTOR * 2) for i in range(2)],
}

instrument_id_mapping = {
    "lf-fem": "OPX1000",
    "mw-fem": "OPX1000",
    "opx+": "OPX+",
    "octave": "Octave",
}

# Define classes for managing annotations and slots
class AnnotationPort:
    def __init__(self, labels, color, con, slot, io_type, port, instrument_id):
        self.labels = labels
        self.color = color
        self.con = con
        self.slot = slot
        self.io_type = io_type
        self.port = port
        self.instrument_id = instrument_id

class LabelSlot:
    def __init__(self, slot, label, con):
        self.slot = slot
        self.label = label
        self.con = con

class InstrumentFigureManager:
    def __init__(self):
        self.figures = {}

    def get_ax(self, con, slot, instrument_id):
        instrument_id = instrument_id_mapping[instrument_id]
        key = f"{instrument_id}_{con}"
        if key not in self.figures:
            if instrument_id == "OPX1000":
                fig, axs = plt.subplots(
                    nrows=1,
                    ncols=8,
                    figsize=(CHASSIS_DIMENSIONS[instrument_id]["width"] * 2,
                             CHASSIS_DIMENSIONS[instrument_id]["height"] * 2))
                for ax in axs.flat:
                    ax.set_ylim([0, 1])
                    ax.axis("off")
                self.figures[key] = axs
            else:
                raise NotImplementedError()
            fig.suptitle(f"{instrument_id} Wiring Diagram - con{con}", fontweight="bold", fontsize=20)
        return self.figures[key][slot] if slot is not None else self.figures[key]

def invert_qubit_dict(qubit_dict):
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

def prepare_annotations(inverted_dict):
    annotations = []
    for key, values in inverted_dict.items():
        con, slot, io_type, port, instrument_id, channel_type = key
        labels = [value[0] for value in values]
        color = get_color_for_line_type(channel_type)
        annotations.append(AnnotationPort(labels, color, con, slot, io_type, port, instrument_id))
    return annotations

def prepare_slot_labels(inverted_dict):
    labels = []
    slots_seen = set()
    for (con, slot, io_type, port, instrument_id, channel_type), values in inverted_dict.items():
        if (con, slot) not in slots_seen:
            label = f"{slot}: {instrument_id}"
            labels.append(LabelSlot(slot, label, con))
            slots_seen.add((con, slot))
    return labels

def draw_annotations(ax, annotations):
    for annotation in annotations:
        pos = PORT_POSITIONS[annotation.instrument_id][annotation.io_type][annotation.port - 1]
        x, y = pos
        fill_color = annotation.color if annotation.labels else "none"
        ax.add_patch(patches.Circle((x, y), 0.1, edgecolor="black", facecolor=fill_color))
        for i, label in enumerate(annotation.labels):
            ax.text(
                x - 0.15,
                y + 0.15 * i,
                label,
                ha="right",
                va="center",
                fontsize=14,
                color="black",
                bbox=dict(facecolor="white", alpha=0.3, edgecolor="none"),
            )

def draw_slot_label(ax, annotation):
    ax.set_title(f"{annotation.slot}: {annotation.instrument_id}", fontweight="bold")

def get_color_for_line_type(line_type):
    color_map = {
        "lf-fem": "blue",
        "mw-fem": "orange",
        "opx+": "yellow",
        "octave": "purple"
    }
    return color_map.get(line_type, "grey")

def visualize_chassis(qubit_dict):
    # Invert the qubit dictionary for easier annotation processing
    inverted_dict = invert_qubit_dict(qubit_dict)

    # Prepare annotations and labels
    annotations = prepare_annotations(inverted_dict)

    # Manage figures and draw
    manager = InstrumentFigureManager()
    for annotation in annotations:
        ax = manager.get_ax(annotation.con, annotation.slot, annotation.instrument_id)
        draw_annotations(ax, annotations)
        draw_slot_label(ax, annotation)

    plt.tight_layout()
    plt.show()
