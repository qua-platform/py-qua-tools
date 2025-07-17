import base64
import datetime
import io
from typing import List, Optional
import matplotlib.pyplot as plt
import webbrowser

import importlib.resources as pkg_resources

from qualang_tools.wirer.instruments.instrument_channels import InstrumentChannels
from qualang_tools.wirer.visualizer.instrument_figure_manager import InstrumentFigureManager
from qualang_tools.wirer import visualizer


class WebInstrumentFigureManager(InstrumentFigureManager):
    """Extended figure manager that can export figures to web format"""

    def __init__(self):
        super().__init__()
        self.figure_objects = {}  # Store actual Figure objects

    def get_ax(self, con: int, slot: int, instrument_id: str):
        # Call parent method to get axes
        ax = super().get_ax(con, slot, instrument_id)

        # Store the figure object for later web export
        instrument_id_mapped = self.instrument_id_mapping.get(instrument_id, instrument_id)
        key = self._key(instrument_id_mapped, con)

        # Find and store the figure
        if isinstance(ax, dict):
            # For OPX1000 with multiple axes
            fig = list(ax.values())[0].figure
        else:
            # For single axis instruments
            fig = ax.figure

        self.figure_objects[key] = fig
        return ax

    def _key(self, instrument_id: str, con: int):
        return f"{instrument_id}_{con}"

    @property
    def instrument_id_mapping(self):
        from qualang_tools.wirer.visualizer.layout import instrument_id_mapping

        return instrument_id_mapping

    def export_figures_to_html(self, output_path: str = "instrument_visualization.html"):
        """Export all figures to a single HTML page"""

        # Convert figures to base64 encoded images
        figure_data = []

        for key, fig in self.figure_objects.items():
            # Remove suptitle to reduce image padding
            if fig._suptitle:
                fig._suptitle.remove()

            # Save figure to bytes buffer
            img_buffer = io.BytesIO()
            fig.patch.set_facecolor("#ffffff")  # Transparent figure background
            fig.savefig(img_buffer, format="png", dpi=150, bbox_inches="tight")
            img_buffer.seek(0)

            # Encode to base64
            img_base64 = base64.b64encode(img_buffer.read()).decode("utf-8")
            img_buffer.close()

            figure_data.append(
                {"key": key, "title": key, "data": img_base64}  # Use key as title since suptitle is removed
            )

        # Move OPX+ and OPX1000 figures to the end
        def priority(fig):
            title = fig["title"].lower()
            if "opx" in title:
                return 1  # Lower priority: appear later
            return 0  # Higher priority: appear first

        figure_data.sort(key=priority)

        # Generate HTML content
        html_content = self._generate_html(figure_data)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Visualization exported to: {output_path}")
        return output_path

    def _generate_html(self, figure_data: List[dict]) -> str:
        """Generate the HTML content with embedded figures"""

        with pkg_resources.files(visualizer).joinpath("web_template.html").open("r", encoding="utf-8") as f:
            html_template = f.read()

        # Generate figure HTML
        figures_html = '<div id="figs">'

        for i, fig_data in enumerate(figure_data):
            figures_html += f"""
            <div class="figure-container">
                <!-- Remove the caption and use the title as tooltip -->
                <p class="figure-caption">{fig_data['title'].replace('_', ' #')}</p>
                <img src="data:image/png;base64,{fig_data['data']}"
                     alt="{fig_data['title']}"
                     title="{fig_data['title'].replace('_', ' #')}"
                     class="figure-image"
                     style="transition: none;">
            </div>"""  # noqa: E272

        figures_html += "</div>"

        return html_template.format(figures_html=figures_html)


def visualize_web(
    qubit_dict,
    available_channels: Optional[InstrumentChannels] = None,
    output_path: str = None,
    show_matplotlib: bool = False,
):
    """
    Create web-based visualization of instrument wiring

    Args:
        qubit_dict: Dictionary of qubit configurations
        available_channels: Available instrument channels (optional)
        output_path: Path for output HTML file
        show_matplotlib: Whether to also show matplotlib windows

    Returns:
        str: Path to generated HTML file
    """
    # Import functions from your existing visualizer
    from qualang_tools.wirer.visualizer.visualizer import (
        invert_qubit_dict,
        make_annotations,
        merge_annotations_on_same_channel,
        make_unused_channel_annotations,
        draw_annotations,
    )

    # Process data same as original visualizer
    inverted_dict = invert_qubit_dict(qubit_dict)
    annotations = make_annotations(inverted_dict)
    annotations = merge_annotations_on_same_channel(annotations)

    # Use web-enabled figure manager
    manager = WebInstrumentFigureManager()

    # Draw unused channels if provided
    if available_channels is not None:
        available_channel_annotations = make_unused_channel_annotations(available_channels)
        draw_annotations(manager, available_channel_annotations)

    # Draw main annotations
    draw_annotations(manager, annotations)

    if output_path is None:
        output_path = f'qm-instrument_config_{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.html'

    # Export to HTML
    html_path = manager.export_figures_to_html(output_path)

    # Optionally show matplotlib windows too
    if show_matplotlib:
        plt.show()
    else:
        # Close matplotlib figures to save memory
        plt.close("all")

    return html_path


def visualize(qubit_dict, available_channels=None, use_matplotlib=None):
    """
    Args:
        qubit_dict: Dictionary of qubit configurations
        available_channels: Available instrument channels (optional)
        use_matplotlib: Whether to show matplotlib windows (new parameter) instead
    """
    if use_matplotlib:
        from qualang_tools.wirer.visualizer.visualizer import (
            invert_qubit_dict,
            make_annotations,
            merge_annotations_on_same_channel,
            make_unused_channel_annotations,
            draw_annotations,
        )

        # Replicate original visualize logic
        inverted_dict = invert_qubit_dict(qubit_dict)
        annotations = make_annotations(inverted_dict)
        annotations = merge_annotations_on_same_channel(annotations)

        manager = InstrumentFigureManager()

        if available_channels is not None:
            available_channel_annotations = make_unused_channel_annotations(available_channels)
            draw_annotations(manager, available_channel_annotations)

        draw_annotations(manager, annotations)
        plt.show()
    else:
        webbrowser.open(visualize_web(qubit_dict, available_channels, show_matplotlib=False))
