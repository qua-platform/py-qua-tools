"""
Replacement tests for enhanced_waveform_report.py
Run with: python -m pytest tests/waveform_report/test_enhanced_waveform_report.py -v
"""

import json
import os
import shutil
import tempfile
import warnings

import pytest
import plotly.graph_objects as go

import qualang_tools.waveform_report.enhanced_report as ewr
from qualang_tools.waveform_report import (
    VerticalMarkerConfig,
    TimingMarker,
    create_waveform_plot_with_markers,
    extract_timing_markers,
)
from qualang_tools.waveform_report.enhanced_report import (
    _merge_nearby_markers,
    _make_marker_shapes,
    _get_y_axis_range,
    _parse_plotly_figure_from_html,
    _clean_pulse_name,
)


def _m(**overrides):
    base = {
        "timestamp_ns": 100.0,
        "marker_type": "start",
        "operation_type": "analog",
        "element": "q1_xy",
        "pulse_name": "x180",
        "controller": "con1",
        "fem": 1,
        "output_ports": [1],
    }
    base.update(overrides)
    return TimingMarker(**base)


def _wf(**overrides):
    base = {
        "timestamp": 100,
        "length": 40,
        "element": "q1_xy",
        "pulse_name": "OriginPulseName=x180",
        "controller": "con1",
        "fem": 1,
        "output_ports": [1],
    }
    base.update(overrides)
    return base


def _wf_dict(analog=None, digital=None, adc=None):
    return {
        "analog_waveforms": analog or [],
        "digital_waveforms": digital or [],
        "adc_acquisitions": adc or [],
    }


def _hover_traces(fig):
    """Filter a figure's traces to only invisible hover-tooltip scatter traces."""
    return [
        t for t in fig.data
        if t.hoverinfo == "text"
        and t.marker is not None
        and t.marker.opacity == 0
    ]


def _run_orchestrator(report, **overrides):
    """Call create_waveform_plot_with_markers with safe defaults."""
    defaults = dict(
        samples=None,
        marker_config=None,
        controllers=None,
        plot=False,
        save_dir=None,
    )
    defaults.update(overrides)
    return create_waveform_plot_with_markers(report, **defaults)


class DummyReport:
    """Mock WaveformReport that mimics QM SDK's create_plot save_path behavior."""

    def __init__(self, waveform_dict, data=None, layout=None, raise_on_create=None):
        self._waveform_dict = waveform_dict
        self.job_id = "dummy_job"
        self._data = data or [{"x": [0, 1], "y": [0, 1], "type": "scatter"}]
        self._layout = layout or {"title": "Dummy Plot"}
        self._raise_on_create = raise_on_create

    def to_dict(self):
        return self._waveform_dict

    def create_plot(self, samples=None, controllers=None, plot=True, save_path=None):
        if self._raise_on_create is not None:
            raise self._raise_on_create

        if save_path is None:
            return

        save_dir = os.path.dirname(save_path)
        if not save_dir:
            save_dir = "."

        html = (
            "<html><head></head><body>"
            "<script>"
            f"Plotly.newPlot('plot', {json.dumps(self._data)}, {json.dumps(self._layout)});"
            "</script></body></html>"
        )

        output_path = os.path.join(
            save_dir, f"waveform_report_con1_{self.job_id}.html"
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)


@pytest.fixture
def single_analog_wf_dict():
    """Waveform dict with one analog pulse (q1_xy, x180, 100-140ns)."""
    return _wf_dict(analog=[_wf()])


@pytest.fixture
def single_analog_report(single_analog_wf_dict):
    """DummyReport wrapping a single analog pulse."""
    return DummyReport(single_analog_wf_dict)


def test_config_defaults():
    config = VerticalMarkerConfig()
    assert config.show_analog_markers is True
    assert config.show_digital_markers is False
    assert config.start_line_color == "rgba(34, 139, 34, 0.6)"
    assert config.end_line_color == "rgba(178, 34, 34, 0.6)"


@pytest.mark.parametrize(
    ("element", "include", "exclude", "expected"),
    [
        ("q1_xy", None, None, True),
        ("q1_xy", ["q1_xy", "q2_xy"], None, True),
        ("rr1", ["q1_xy", "q2_xy"], None, False),
        ("q2_xy", ["q1_xy", "q2_xy"], ["q2_xy"], False),
    ],
)
def test_should_include(element, include, exclude, expected):
    config = VerticalMarkerConfig(
        elements_to_include=include,
        elements_to_exclude=exclude,
    )
    assert config.should_include(element) is expected


def test_color_for():
    config = VerticalMarkerConfig(
        start_line_color="rgba(0, 0, 255, 0.5)",
        end_line_color="rgba(255, 0, 0, 0.5)",
    )
    assert config.color_for("start") == "rgba(0, 0, 255, 0.5)"
    assert config.color_for("end") == "rgba(255, 0, 0, 0.5)"


@pytest.mark.parametrize(
    ("marker_type", "op_type", "element", "pulse", "expected"),
    [
        ("start", "analog", "q1_xy", "x180", "Start [Pulse]: x180 (q1_xy)"),
        ("end", "digital", "rr1", "ON", "End [Digital]: ON (rr1)"),
        ("start", "adc", "rr1", "acquisition", "Start [Integration]: acquisition (rr1)"),
    ],
)
def test_hover_text(marker_type, op_type, element, pulse, expected):
    marker = _m(
        marker_type=marker_type,
        operation_type=op_type,
        element=element,
        pulse_name=pulse,
    )
    assert marker.hover_text == expected


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (None, "unknown"),
        ("", "unknown"),
        ("OriginPulseName=x180", "x180"),
        ("x180", "x180"),
    ],
)
def test_clean_pulse_name(name, expected):
    assert _clean_pulse_name(name) == expected


def test_extract_analog():
    waveform_dict = _wf_dict(analog=[_wf()])

    markers = extract_timing_markers(waveform_dict, VerticalMarkerConfig())

    assert len(markers) == 2
    assert markers[0].timestamp_ns == 100
    assert markers[1].timestamp_ns == 140
    assert markers[0].pulse_name == "x180"


def test_extract_adc():
    waveform_dict = _wf_dict(
        adc=[
            {
                "start_time": 500,
                "end_time": 1500,
                "quantum_element": "rr1",
                "process": "full",
                "controller": "con1",
                "fem": 1,
                "adc_ports": [1, 2],
            }
        ]
    )

    markers = extract_timing_markers(waveform_dict, VerticalMarkerConfig())

    assert len(markers) == 2
    assert markers[0].timestamp_ns == 500
    assert markers[0].operation_type == "adc"
    assert markers[0].element == "rr1"
    assert markers[0].output_ports == [1, 2]
    assert markers[1].timestamp_ns == 1500


def test_extract_digital_opt_in():
    waveform_dict = _wf_dict(
        digital=[
            _wf(
                timestamp=200,
                length=100,
                element="rr1",
                pulse_name="ON",
                output_ports=[5],
            )
        ]
    )

    markers = extract_timing_markers(waveform_dict, VerticalMarkerConfig())
    assert markers == []

    config = VerticalMarkerConfig(show_digital_markers=True)
    markers = extract_timing_markers(waveform_dict, config)
    assert len(markers) == 2
    assert markers[0].operation_type == "digital"


@pytest.mark.parametrize(
    ("include", "exclude", "expected_elements"),
    [
        (["q1_xy"], None, {"q1_xy"}),
        (None, ["q1_xy"], {"q2_xy"}),
        (["q1_xy", "q2_xy"], ["q2_xy"], {"q1_xy"}),
    ],
)
def test_element_filtering(include, exclude, expected_elements):
    waveform_dict = _wf_dict(
        analog=[
            _wf(timestamp=100, element="q1_xy", output_ports=[1]),
            _wf(timestamp=200, element="q2_xy", output_ports=[2]),
        ]
    )

    config = VerticalMarkerConfig(
        elements_to_include=include,
        elements_to_exclude=exclude,
    )
    markers = extract_timing_markers(waveform_dict, config)

    assert {m.element for m in markers} == expected_elements


def test_duration_filtering():
    waveform_dict = _wf_dict(
        analog=[
            _wf(length=5, pulse_name="short"),
            _wf(timestamp=200, pulse_name="long"),
        ]
    )

    config = VerticalMarkerConfig(min_duration_ns=10.0)
    markers = extract_timing_markers(waveform_dict, config)

    assert len(markers) == 2
    assert markers[0].pulse_name == "long"


def test_empty_input():
    assert extract_timing_markers({}, VerticalMarkerConfig()) == []


def test_sorted_output():
    waveform_dict = _wf_dict(
        analog=[
            _wf(timestamp=300, element="q2_xy", output_ports=[2]),
            _wf(),
        ]
    )

    markers = extract_timing_markers(waveform_dict, VerticalMarkerConfig())
    timestamps = [m.timestamp_ns for m in markers]
    assert timestamps == sorted(timestamps)


def test_null_pulse_name_regression():
    waveform_dict = _wf_dict(analog=[_wf(pulse_name=None)])

    markers = extract_timing_markers(waveform_dict, VerticalMarkerConfig())
    assert markers[0].pulse_name == "unknown"


def test_merge_within_threshold():
    markers = [
        _m(timestamp_ns=100, marker_type="start"),
        _m(timestamp_ns=102, marker_type="start"),
        _m(timestamp_ns=104, marker_type="start"),
    ]

    merged = _merge_nearby_markers(markers, threshold_ns=5.0)

    assert len(merged) == 1
    assert merged[0].timestamp_ns == 102.0


def test_merge_preserves_distant():
    markers = [
        _m(timestamp_ns=100, marker_type="start"),
        _m(timestamp_ns=200, marker_type="start"),
    ]

    merged = _merge_nearby_markers(markers, threshold_ns=5.0)

    assert len(merged) == 2
    assert [m.timestamp_ns for m in merged] == [100, 200]


def test_merge_groups_by_marker_type():
    markers = [
        _m(timestamp_ns=100, marker_type="start"),
        _m(timestamp_ns=102, marker_type="end"),
    ]

    merged = _merge_nearby_markers(markers, threshold_ns=5.0)

    assert len(merged) == 2
    assert {m.marker_type for m in merged} == {"start", "end"}


def test_merge_groups_by_operation_type():
    markers = [
        _m(timestamp_ns=100, marker_type="start", operation_type="analog"),
        _m(timestamp_ns=102, marker_type="start", operation_type="digital"),
    ]

    merged = _merge_nearby_markers(markers, threshold_ns=5.0)

    assert len(merged) == 2
    assert {m.operation_type for m in merged} == {"analog", "digital"}


def test_merge_preserves_metadata():
    markers = [
        _m(
            timestamp_ns=100,
            element="q1_xy",
            pulse_name="x180",
            controller="con1",
            fem=1,
            output_ports=[1],
        ),
        _m(
            timestamp_ns=102,
            element="q2_xy",
            pulse_name="y90",
            controller="con2",
            fem=2,
            output_ports=[2, 3],
        ),
    ]

    merged = _merge_nearby_markers(markers, threshold_ns=5.0)

    assert len(merged) == 1
    assert merged[0].element == "q1_xy"
    assert merged[0].pulse_name == "x180"
    assert merged[0].controller == "con1"
    assert merged[0].fem == 1
    assert merged[0].output_ports == [1]


@pytest.mark.parametrize(
    ("markers", "threshold_ns", "expected_len"),
    [
        ([], 5.0, 0),
        ([_m(timestamp_ns=100), _m(timestamp_ns=102)], 0, 2),
        ([_m(timestamp_ns=100), _m(timestamp_ns=102)], -1.0, 2),
    ],
)
def test_merge_edge_cases(markers, threshold_ns, expected_len):
    merged = _merge_nearby_markers(markers, threshold_ns=threshold_ns)
    assert len(merged) == expected_len


def test_shape_structure_and_colors():
    markers = [
        _m(timestamp_ns=100, marker_type="start"),
        _m(timestamp_ns=140, marker_type="end"),
    ]
    config = VerticalMarkerConfig(
        start_line_color="rgba(0, 0, 255, 0.5)",
        end_line_color="rgba(255, 0, 0, 0.5)",
        show_hover_info=True,
    )
    shapes = _make_marker_shapes(markers, config)

    assert len(shapes) == 2
    for shape, marker in zip(shapes, markers):
        assert shape["type"] == "line"
        assert shape["xref"] == "x"
        assert shape["yref"] == "paper"
        assert shape["x0"] == marker.timestamp_ns
        assert shape["x1"] == marker.timestamp_ns
        assert shape["y0"] == 0
        assert shape["y1"] == 1
        assert isinstance(shape["line"], dict)
        assert shape["name"] == marker.hover_text

    assert shapes[0]["line"]["color"] == "rgba(0, 0, 255, 0.5)"
    assert shapes[1]["line"]["color"] == "rgba(255, 0, 0, 0.5)"


def test_shape_hover_name_absent_when_disabled():
    config = VerticalMarkerConfig(show_hover_info=False)
    marker = _m(timestamp_ns=100, marker_type="start")
    shapes = _make_marker_shapes([marker], config)

    assert "name" not in shapes[0]


def test_parse_valid_html():
    html = (
        "<html><head></head><body>"
        "<script>"
        "Plotly.newPlot('plot', [{\"x\": [0, 1], \"y\": [1, 2], \"type\": \"scatter\"}], "
        "{\"title\": \"Plot\"});"
        "</script></body></html>"
    )
    fig = _parse_plotly_figure_from_html(html)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 1
    assert fig.layout.title.text == "Plot"


def test_parse_invalid_html():
    with pytest.raises(RuntimeError):
        _parse_plotly_figure_from_html("not a plotly html")


def test_explicit_range():
    fig = go.Figure()
    fig.update_layout(yaxis=dict(range=[-2, 2]))

    assert _get_y_axis_range(fig, "y") == (-2, 2)


def test_computed_from_traces():
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[10, 20]))

    assert _get_y_axis_range(fig, "y") == (10, 20)


def test_empty_figure_default():
    fig = go.Figure()
    assert _get_y_axis_range(fig, "y") == (-1, 1)


def test_returns_figure_with_shapes(single_analog_report):
    fig = _run_orchestrator(single_analog_report)

    assert isinstance(fig, go.Figure)
    assert fig.layout.shapes is not None
    assert len(fig.layout.shapes) == 2

    config = VerticalMarkerConfig()
    colors = [shape["line"]["color"] for shape in fig.layout.shapes]
    assert config.start_line_color in colors
    assert config.end_line_color in colors


def test_hover_traces_added(single_analog_report):
    config = VerticalMarkerConfig(show_hover_info=True)
    fig = _run_orchestrator(single_analog_report, marker_config=config)

    hover_traces = _hover_traces(fig)
    assert len(hover_traces) >= 1


def test_hover_disabled_no_traces(single_analog_report):
    config = VerticalMarkerConfig(show_hover_info=False)
    fig = _run_orchestrator(single_analog_report, marker_config=config)

    hover_traces = _hover_traces(fig)
    assert len(hover_traces) == 0


def test_hover_correct_text(single_analog_report):
    config = VerticalMarkerConfig(show_hover_info=True, merge_threshold_ns=0)
    fig = _run_orchestrator(single_analog_report, marker_config=config)

    hover_traces = _hover_traces(fig)
    all_texts = []
    for trace in hover_traces:
        all_texts.extend(trace.hovertext)

    assert "Start [Pulse]: x180 (q1_xy)" in all_texts
    assert "End [Pulse]: x180 (q1_xy)" in all_texts


def test_hover_multi_subplot(monkeypatch):
    waveform_dict = _wf_dict(analog=[_wf()])
    data = [
        {"x": [0, 100, 200], "y": [0.1, 0.5, 0.2], "type": "scatter", "yaxis": "y"},
        {"x": [0, 100, 200], "y": [-0.3, 0.0, 0.3], "type": "scatter", "yaxis": "y2"},
        {"x": [0, 100, 200], "y": [1, 0, 1], "type": "scatter", "yaxis": "y3"},
    ]
    layout = {
        "title": "Dummy Plot",
        "yaxis": {"domain": [0.7, 1.0]},
        "yaxis2": {"domain": [0.35, 0.65]},
        "yaxis3": {"domain": [0.0, 0.3]},
    }
    waveform_report = DummyReport(waveform_dict, data=data, layout=layout)

    def _stub_load_sdk_figure(report, samples, controllers):
        return go.Figure(data=data, layout=layout)

    monkeypatch.setattr(ewr, "_load_sdk_figure", _stub_load_sdk_figure)

    config = VerticalMarkerConfig(show_hover_info=True, merge_threshold_ns=0)
    fig = _run_orchestrator(waveform_report, marker_config=config)

    hover_traces = _hover_traces(fig)
    assert len(hover_traces) == 3

    yaxes_used = {getattr(t, "yaxis", "y") or "y" for t in hover_traces}
    assert yaxes_used == {"y", "y2", "y3"}

    for trace in hover_traces:
        xax = getattr(trace, "xaxis", None) or "x"
        assert xax == "x"


def test_hover_points_per_marker(single_analog_report):
    config = VerticalMarkerConfig(
        show_hover_info=True,
        merge_threshold_ns=0,
        hover_points_per_marker=5,
    )
    fig = _run_orchestrator(single_analog_report, marker_config=config)

    hover_traces = _hover_traces(fig)
    assert len(hover_traces) == 1
    assert len(hover_traces[0].x) == 10
    assert len(hover_traces[0].y) == 10
    assert min(hover_traces[0].y) == 0
    assert max(hover_traces[0].y) == 1


def test_fallback_on_sdk_failure():
    waveform_report = DummyReport(_wf_dict(), raise_on_create=RuntimeError("boom"))

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        fig = _run_orchestrator(waveform_report)

    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == (
        "Waveform Report (marker overlay only - could not parse SDK output)"
    )
    assert any("Could not load SDK HTML:" in str(w.message) for w in caught)


def test_temp_dir_cleaned_up(monkeypatch):
    original_mkdtemp = tempfile.mkdtemp
    created = {}
    rmtree_calls = []

    def _mkdtemp(prefix="tmp", **kwargs):
        path = original_mkdtemp(prefix=prefix)
        created["path"] = path
        return path

    monkeypatch.setattr(ewr.tempfile, "mkdtemp", _mkdtemp)

    def _rmtree(path, ignore_errors=False):
        rmtree_calls.append(path)
        try:
            os.rmdir(path)
        except OSError:
            if not ignore_errors:
                raise

    monkeypatch.setattr(ewr.shutil, "rmtree", _rmtree)

    waveform_report = DummyReport(_wf_dict())
    monkeypatch.setattr(waveform_report, "create_plot", lambda **kw: None)

    fig = _run_orchestrator(waveform_report)

    assert isinstance(fig, go.Figure)

    created_path = created.get("path")
    assert created_path is not None
    assert created_path in rmtree_calls
    if os.path.exists(created_path):
        shutil.rmtree(created_path, ignore_errors=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
