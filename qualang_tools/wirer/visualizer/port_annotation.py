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
        for i, label in enumerate(self.labels):
            # port annotation
            ax.text(
                x,
                y,
                str(self.port),
                ha="center",
                va="center",
                fontsize=10,
                color=get_contrast_color(self.color),
                # fontweight="bold",
            )
            # qubit line annotation
            ax.text(
                x - PORT_SPACING_FACTOR / 1.75,
                y + (PORT_SPACING_FACTOR/2) * i,
                label,
                ha="right",
                va="center",
                fontsize=14,
                # fontweight="bold",
                color="black",
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