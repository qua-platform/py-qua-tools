from __future__ import annotations

"""
Enhanced Waveform Report with Vertical Timeline Markers

This module wraps the QM SDK's waveform report functionality and adds
vertical timeline markers that span all subplot rows, making it easier
to correlate timing across different output channels.

Usage:
    from qualang_tools.waveform_report import create_waveform_plot_with_markers, VerticalMarkerConfig

    fig = create_waveform_plot_with_markers(
        waveform_report,
        samples,
        marker_config=VerticalMarkerConfig(),
        plot=True,
        save_dir="./output"
    )
"""

# NOTE: The QM SDK HTML/Plotly output format is not guaranteed stable.
# Keep the parsing logic defensive and update if the SDK output changes.

# === IMPORTS ===
from collections import defaultdict
from dataclasses import dataclass
import logging
from typing import List, Dict, Any, Literal
import warnings
import plotly.graph_objects as go
import json
import re
from pathlib import Path
import shutil
import tempfile

logger = logging.getLogger(__name__)
# Note: This module uses warnings.warn() for suppressible user-facing issues
# (e.g., SDK parsing failures) and logger for informational messages.

__all__ = [
    "VerticalMarkerConfig",
    "TimingMarker",
    "create_waveform_plot_with_markers",
    "extract_timing_markers",
]

# === CONFIGURATION ===
MarkerType = Literal["start", "end"]
OperationType = Literal["analog", "digital", "adc"]


@dataclass
class VerticalMarkerConfig:
    """Configuration for vertical timeline markers.

    Attributes:
        show_analog_markers: Include markers for analog waveforms
        show_digital_markers: Include markers for digital waveforms
        show_adc_markers: Include markers for ADC acquisitions
        start_line_color: RGBA color for operation start markers
        end_line_color: RGBA color for operation end markers
        line_width: Width of marker lines in pixels
        line_dash: Line style - "solid", "dot", "dash", "longdash", "dashdot"
        min_duration_ns: Ignore operations shorter than this (nanoseconds)
        merge_threshold_ns: Merge markers within this threshold (nanoseconds)
        elements_to_include: Only show markers for these elements (None = all)
        elements_to_exclude: Hide markers for these elements (None = none)
        show_hover_info: Enable hover tooltips on markers
        hover_marker_size: Size of invisible hover markers in pixels (default 15)
    """
    show_analog_markers: bool = True
    show_digital_markers: bool = False
    show_adc_markers: bool = True
    start_line_color: str = "rgba(34, 139, 34, 0.6)"   # Forest green
    end_line_color: str = "rgba(178, 34, 34, 0.6)"     # Firebrick red
    line_width: float = 1.0
    line_dash: str = "dot"
    min_duration_ns: float = 0.0
    merge_threshold_ns: float = 4.0
    elements_to_include: list[str] | None = None
    elements_to_exclude: list[str] | None = None
    show_hover_info: bool = True
    hover_marker_size: int = 15
    hover_points_per_marker: int = 20

    def color_for(self, marker_type: MarkerType) -> str:
        return self.start_line_color if marker_type == "start" else self.end_line_color

    def should_include(self, element: str) -> bool:
        if self.elements_to_include is not None:
            if element not in self.elements_to_include:
                return False

        if self.elements_to_exclude is not None:
            if element in self.elements_to_exclude:
                return False

        return True


# === DATA CLASSES ===
_OPERATION_TYPE_LABELS = {
    "analog": "Pulse",
    "digital": "Digital",
    "adc": "Integration",
}


@dataclass(frozen=True)
class TimingMarker:
    """Represents a single timing marker (start or end of an operation).

    Attributes:
        timestamp_ns: Time position in nanoseconds
        marker_type: Either "start" or "end"
        operation_type: Either "analog", "digital", or "adc"
        element: Name of the quantum element
        pulse_name: Name of the pulse/operation
        controller: Controller name (e.g., "con1")
        fem: FEM module number
        output_ports: List of physical output port numbers
    """
    timestamp_ns: float
    marker_type: MarkerType  # "start" or "end"
    operation_type: OperationType  # "analog", "digital", "adc"
    element: str
    pulse_name: str
    controller: str
    fem: int
    output_ports: List[int]

    @property
    def hover_text(self) -> str:
        """Generate hover tooltip text for this marker."""
        type_label = _OPERATION_TYPE_LABELS.get(
            self.operation_type, self.operation_type
        )
        return (
            f"{self.marker_type.capitalize()} [{type_label}]: "
            f"{self.pulse_name} ({self.element})"
        )


def _merge_nearby_markers(
    markers: List[TimingMarker],
    threshold_ns: float
) -> List[TimingMarker]:
    """Merge markers that are within threshold_ns of each other.

    Markers are only merged if they have the same marker_type (start/end)
    AND the same operation_type (analog/digital/adc).  This prevents a
    digital marker from absorbing a nearby ADC (integration) marker, which
    would cause the merged result to lose the [Integration] label.

    When merged, the first marker's metadata is kept but the timestamp
    is averaged.

    Args:
        markers: Sorted list of timing markers
        threshold_ns: Maximum time difference for merging (nanoseconds)

    Returns:
        New sorted list with nearby markers merged
    """
    if not markers or threshold_ns <= 0:
        return markers

    # Separate by (marker_type, operation_type) so we never merge across
    # different operation types (e.g. digital + adc).
    groups: Dict[tuple, List[TimingMarker]] = defaultdict(list)
    for m in markers:
        groups[(m.marker_type, m.operation_type)].append(m)

    def merge_group(group: List[TimingMarker]) -> List[TimingMarker]:
        """Merge markers within a single type group."""
        if not group:
            return []

        # Sort by timestamp
        sorted_group = sorted(group, key=lambda m: m.timestamp_ns)
        merged = []

        i = 0
        while i < len(sorted_group):
            # Start a new cluster with this marker
            cluster = [sorted_group[i]]
            j = i + 1

            # Add all markers within threshold
            while j < len(sorted_group):
                if sorted_group[j].timestamp_ns - cluster[-1].timestamp_ns <= threshold_ns:
                    cluster.append(sorted_group[j])
                    j += 1
                else:
                    break

            # Create merged marker using first marker's metadata
            # but with averaged timestamp
            avg_timestamp = sum(m.timestamp_ns for m in cluster) / len(cluster)
            merged_marker = TimingMarker(
                timestamp_ns=avg_timestamp,
                marker_type=cluster[0].marker_type,
                operation_type=cluster[0].operation_type,
                element=cluster[0].element,
                pulse_name=cluster[0].pulse_name,
                controller=cluster[0].controller,
                fem=cluster[0].fem,
                output_ports=cluster[0].output_ports
            )
            merged.append(merged_marker)

            i = j

        return merged

    # Merge each group separately
    result = []
    for group in groups.values():
        result.extend(merge_group(group))

    # Re-sort by timestamp
    result.sort(key=lambda m: m.timestamp_ns)

    return result


def _get_y_axis_range(fig: go.Figure, yaxis_ref: str) -> tuple:
    """Get the (y_min, y_max) range of a y-axis for hover trace positioning.

    Attempts to read the axis range from the figure layout. If the range
    is not explicitly set (auto-ranged), computes the range from the
    trace data on that axis. Falls back to (-1, 1) if no data is available.

    Args:
        fig: The Plotly figure to inspect.
        yaxis_ref: Y-axis reference string (e.g., 'y', 'y2', 'y3').

    Returns:
        Tuple of (y_min, y_max) for the axis range.
    """
    # Map 'y' -> 'yaxis', 'y2' -> 'yaxis2', etc.
    layout_key = "yaxis" if yaxis_ref == "y" else f"yaxis{yaxis_ref[1:]}"
    axis_obj = fig.layout[layout_key]

    if axis_obj is not None and axis_obj.range is not None:
        return (axis_obj.range[0], axis_obj.range[1])

    # Fallback: compute from trace data on this axis
    y_values = []
    for trace in fig.data:
        trace_yaxis = getattr(trace, "yaxis", None) or "y"
        if trace_yaxis == yaxis_ref and hasattr(trace, "y") and trace.y is not None:
            for v in trace.y:
                if isinstance(v, (int, float)):
                    y_values.append(v)

    if y_values:
        return (min(y_values), max(y_values))

    return (-1, 1)


def _clean_pulse_name(name: str | None) -> str:
    name = name or "unknown"
    return name.removeprefix("OriginPulseName=")


def _parse_plotly_figure_from_html(html: str) -> go.Figure:
    """Parse a Plotly Figure from the SDK-generated HTML."""
    plotly_call_match = re.search(
        r'Plotly\.newPlot\s*\(\s*["\'][^"\']+["\']\s*,\s*',
        html
    )
    if not plotly_call_match:
        raise RuntimeError("Could not find Plotly.newPlot call in HTML.")

    data_start = plotly_call_match.end()
    decoder = json.JSONDecoder()
    try:
        data, data_end_idx = decoder.raw_decode(html, data_start)
        separator_match = re.search(r'\s*,\s*', html[data_end_idx:])
        if not separator_match:
            raise RuntimeError("Could not locate layout separator after data.")
        layout_start = data_end_idx + separator_match.end()
        layout, _ = decoder.raw_decode(html, layout_start)
    except (json.JSONDecodeError, ValueError) as exc:
        raise RuntimeError(f"Could not parse Plotly figure from HTML: {exc}") from exc

    return go.Figure(data=data, layout=layout)


def _load_sdk_figure(
    report: Any,
    samples: Any,
    controllers: List[str] | None
) -> go.Figure:
    """Generate and parse the SDK HTML into a Plotly Figure."""
    try:
        tmpdir = tempfile.mkdtemp(prefix="enhanced_wfr_")
        save_path_for_sdk = str(Path(tmpdir) / "report")
        report.create_plot(
            samples=samples,
            controllers=controllers,
            plot=False,
            save_path=save_path_for_sdk
        )

        html_files = list(Path(tmpdir).glob("*.html"))
        if not html_files:
            raise RuntimeError("SDK did not generate an HTML file.")
        if len(html_files) > 1:
            warnings.warn(
                f"SDK generated multiple HTML files; using {html_files[0].name}."
            )

        html_content = html_files[0].read_text(encoding="utf-8")
        return _parse_plotly_figure_from_html(html_content)
    finally:
        if "tmpdir" in locals():
            shutil.rmtree(tmpdir, ignore_errors=True)


def _extract_source_markers(
    waveforms: List[Dict[str, Any]],
    config: VerticalMarkerConfig,
    *,
    op_type: OperationType,
    elem_field: str,
    name_field: str,
    ports_field: str,
    time_start: str,
    time_end: str | None = None,
    time_length: str | None = None
) -> List[TimingMarker]:
    if (time_end is None) == (time_length is None):
        raise ValueError("Exactly one of time_end or time_length must be provided.")

    markers: List[TimingMarker] = []
    for wf in waveforms:
        element = wf.get(elem_field, "")
        if not config.should_include(element):
            continue

        start_time = wf.get(time_start, 0)
        if time_end is not None:
            end_time = wf.get(time_end, 0)
            duration = end_time - start_time
        else:
            duration = wf.get(time_length, 0)
            end_time = start_time + duration

        if duration < config.min_duration_ns:
            continue

        pulse_name = _clean_pulse_name(wf.get(name_field))
        controller = wf.get("controller", "")
        fem = wf.get("fem", 0)
        ports = wf.get(ports_field, [])

        markers.append(TimingMarker(
            timestamp_ns=start_time,
            marker_type="start",
            operation_type=op_type,
            element=element,
            pulse_name=pulse_name,
            controller=controller,
            fem=fem,
            output_ports=ports
        ))
        markers.append(TimingMarker(
            timestamp_ns=end_time,
            marker_type="end",
            operation_type=op_type,
            element=element,
            pulse_name=pulse_name,
            controller=controller,
            fem=fem,
            output_ports=ports
        ))

    return markers


# === CORE FUNCTIONS ===
def extract_timing_markers(
    waveform_dict: Dict[str, Any],
    config: VerticalMarkerConfig
) -> List[TimingMarker]:
    """Extract timing markers from waveform report dictionary.

    Args:
        waveform_dict: Output from waveform_report.to_dict()
        config: Configuration for filtering markers

    Returns:
        Sorted list of TimingMarker objects

    Reference - waveform_dict structure:
        {
            "analog_waveforms": [
                {"timestamp": 224, "length": 40, "element": "q1_xy",
                 "pulse_name": "OriginPulseName=x180", "controller": "con1",
                 "fem": 1, "output_ports": [1], ...}
            ],
            "digital_waveforms": [...],
            "adc_acquisitions": [
                {"start_time": 500, "end_time": 1500, "quantum_element": "rr1",
                 "controller": "con1", "fem": 1, "adc_ports": [1, 2], ...}
            ]
        }
    """
    markers: List[TimingMarker] = []

    if config.show_analog_markers:
        markers.extend(_extract_source_markers(
            waveform_dict.get("analog_waveforms", []),
            config,
            op_type="analog",
            elem_field="element",
            name_field="pulse_name",
            ports_field="output_ports",
            time_start="timestamp",
            time_length="length"
        ))

    if config.show_digital_markers:
        markers.extend(_extract_source_markers(
            waveform_dict.get("digital_waveforms", []),
            config,
            op_type="digital",
            elem_field="element",
            name_field="pulse_name",
            ports_field="output_ports",
            time_start="timestamp",
            time_length="length"
        ))

    if config.show_adc_markers:
        markers.extend(_extract_source_markers(
            waveform_dict.get("adc_acquisitions", []),
            config,
            op_type="adc",
            elem_field="quantum_element",
            name_field="process",
            ports_field="adc_ports",
            time_start="start_time",
            time_end="end_time"
        ))

    markers.sort(key=lambda m: m.timestamp_ns)
    return markers


def _make_marker_shapes(
    markers: List[TimingMarker],
    config: VerticalMarkerConfig
) -> List[Dict[str, Any]]:
    """Generate Plotly shape dictionaries for vertical lines."""
    return [
        {
            "type": "line",
            "xref": "x",
            "yref": "paper",
            "x0": marker.timestamp_ns,
            "x1": marker.timestamp_ns,
            "y0": 0,
            "y1": 1,
            "line": {
                "color": config.color_for(marker.marker_type),
                "width": config.line_width,
                "dash": config.line_dash,
            },
            **({"name": marker.hover_text} if config.show_hover_info else {}),
        }
        for marker in markers
    ]


def _add_hover_traces(
    fig: go.Figure,
    markers: List[TimingMarker],
    config: VerticalMarkerConfig,
) -> None:
    """Add batched invisible scatter traces for hover tooltips on vertical markers."""
    if not config.show_hover_info or not markers:
        return

    y_to_x_axis: Dict[str, str] = {}
    y_axes = set()
    for trace in fig.data:
        yaxis_ref = getattr(trace, "yaxis", None) or "y"
        xaxis_ref = getattr(trace, "xaxis", None) or "x"
        y_axes.add(yaxis_ref)
        if yaxis_ref not in y_to_x_axis:
            y_to_x_axis[yaxis_ref] = xaxis_ref
    if not y_axes:
        y_axes = {"y"}

    points_per_marker = max(1, int(config.hover_points_per_marker))

    for yaxis_ref in sorted(
        y_axes, key=lambda s: int(s[1:]) if len(s) > 1 else 0
    ):
        y_min, y_max = _get_y_axis_range(fig, yaxis_ref)
        xaxis_ref = y_to_x_axis.get(yaxis_ref, "x")

        if points_per_marker == 1:
            y_points = [(y_min + y_max) / 2]
        else:
            y_points = [
                y_min + i * (y_max - y_min) / (points_per_marker - 1)
                for i in range(points_per_marker)
            ]

        expanded_x = []
        expanded_y = []
        expanded_texts = []
        expanded_colors = []
        for marker in markers:
            color = config.color_for(marker.marker_type)
            for y_pt in y_points:
                expanded_x.append(marker.timestamp_ns)
                expanded_y.append(y_pt)
                expanded_texts.append(marker.hover_text)
                expanded_colors.append(color)

        batch_trace = go.Scatter(
            x=expanded_x,
            y=expanded_y,
            mode="markers",
            marker=dict(size=config.hover_marker_size, opacity=0, color=expanded_colors),
            hoverinfo="text",
            hovertext=expanded_texts,
            showlegend=False,
            xaxis=xaxis_ref,
            yaxis=yaxis_ref,
        )
        fig.add_trace(batch_trace)


# === MAIN API ===
def create_waveform_plot_with_markers(
    waveform_report,
    samples=None,
    marker_config: VerticalMarkerConfig | None = None,
    controllers: list[str] | None = None,
    plot: bool = True,
    save_dir: str | None = None
) -> go.Figure:
    """Create an enhanced waveform visualization with vertical timing markers.

    This function wraps the QM SDK's waveform report visualization and adds
    vertical lines marking operation start/end times across all subplots.

    Args:
        waveform_report: WaveformReport from job.get_simulated_waveform_report()
        samples: SimulatorSamples from job.get_simulated_samples() (optional)
        marker_config: Configuration for vertical markers (uses defaults if None)
        controllers: List of controllers to include (None = all)
        plot: Whether to display the plot in browser
        save_dir: Directory to save the HTML file (None = don't save)

    Returns:
        Plotly Figure object for further customization
    """
    config = marker_config or VerticalMarkerConfig()

    waveform_dict = waveform_report.to_dict()
    markers = extract_timing_markers(waveform_dict, config)
    if config.merge_threshold_ns > 0:
        markers = _merge_nearby_markers(markers, config.merge_threshold_ns)

    try:
        fig = _load_sdk_figure(waveform_report, samples, controllers)
    except Exception as exc:
        warnings.warn(f"Could not load SDK HTML: {exc}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines"))
        fig.update_layout(
            title="Waveform Report (marker overlay only - could not parse SDK output)",
            xaxis_title="Time (ns)"
        )

    shapes = _make_marker_shapes(markers, config)
    existing_shapes = list(fig.layout.shapes) if fig.layout.shapes else []
    fig.update_layout(shapes=existing_shapes + shapes)

    _add_hover_traces(fig, markers, config)

    if plot:
        fig.show()

    if save_dir:
        save_dir_path = Path(save_dir)
        save_dir_path.mkdir(parents=True, exist_ok=True)
        job_id = getattr(waveform_report, "job_id", "unknown")
        filename = f"enhanced_waveform_report_{job_id}.html"
        output_path = save_dir_path / filename
        fig.write_html(str(output_path))
        logger.info("Enhanced waveform report saved to: %s", output_path)

    return fig
