import re
from collections import defaultdict
from typing import List

from matplotlib import patches
from matplotlib.axes import Axes
import matplotlib.colors as mcolors

from .constants import PORT_POSITIONS, PORT_SIZE, PORT_SPACING_FACTOR

class PortAnnotation:
    def __init__(self, labels, color, con, slot, io_type, port, instrument_id):
        self.labels = labels
        self.color = color
        self.con = con
        self.slot = slot
        self.io_type = io_type
        self.port = port
        self.instrument_id = instrument_id

    def draw(self, ax: Axes):
        pos = PORT_POSITIONS[self.instrument_id][self.io_type][self.port - 1]
        x, y = pos
        fill_color = self.color if self.labels else "none"
        ax.add_patch(patches.Circle((x, y), PORT_SIZE, edgecolor="black", facecolor=fill_color))
        labels = combine_labels_for_same_line_type(self.labels)
        for i, label in enumerate(labels):
            # qubit line annotation
            ax.text(
                x - PORT_SPACING_FACTOR / 1.75,
                y + (PORT_SPACING_FACTOR/2) * i,
                label,
                ha="right",
                va="center",
                fontsize=14,
                color="black",
                bbox=dict(facecolor="white", alpha=1, edgecolor="none"),
            )
        # port annotation
        ax.text(
            x,
            y,
            str(self.port),
            ha="center",
            va="center",
            fontsize=10,
            color=get_contrast_color(self.color),
        )
        ax.set_facecolor('lightgrey')

    def title_axes(self, ax: Axes):
        ax.set_title(f"{self.slot}: {self.instrument_id}", fontweight="bold", y=-0.1, va="bottom")


def get_contrast_color(color):
    """
    Returns black or white depending on the luminance of the input color.

    Parameters:
    color (str or tuple): The color to evaluate. Can be a string ('red', '#00FF00', etc.)
                          or an RGB tuple ((1, 0, 0), (0.5, 0.5, 0.5), etc.)

    Returns:
    str: 'black' if the input color is light, 'white' if it is dark.
    """
    # Convert color to RGB format if it's a string
    rgb = mcolors.to_rgb(color)

    # Calculate luminance
    luminance = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]

    # Return 'black' if luminance is high (light color), 'white' if luminance is low (dark color)
    return 'black' if luminance > 0.5 else 'white'

def combine_labels_for_same_line_type(labels: List[str]):
    # Dictionary to group strings by line type
    grouped_lines = defaultdict(list)

    # Regular expression to parse the qubit line label
    pattern = re.compile(r'q(\d+)\.(.+)')

    # Parse each string and group by line type
    for s in labels:
        match = pattern.match(s)
        if match:
            index = int(match.group(1))  # Extract the qubit index
            line_type = match.group(2)  # Extract the line type
            grouped_lines[line_type].append(index)

    # Result list to store the reduced strings
    reduced_strings = []

    # Process each line type group
    for line_type, indices in grouped_lines.items():
        smallest_index = min(indices)
        largest_index = max(indices)
        # Check if there's only one index
        if smallest_index == largest_index:
            reduced_string = f'q{smallest_index}.{line_type}'
        else:
            reduced_string = f'q{smallest_index}-{largest_index}.{line_type}'

        reduced_strings.append(reduced_string)

    return reduced_strings