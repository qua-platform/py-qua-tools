import copy
import pytest
import plotly.graph_objs as go
from qualang_tools.results.data_handler.data_processors import PlotlyGraphSaver
from test_utils import module_installed, dicts_equal


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_no_figures():
    plotly_saver = PlotlyGraphSaver()
    data = {"a": 1, "b": 2, "c": 3}
    assert plotly_saver.process(data) == data


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_suffixes():
    plotly_saver = PlotlyGraphSaver()
    assert plotly_saver.file_format == "html"
    assert plotly_saver.file_suffix == ".html"

    plotly_saver = PlotlyGraphSaver(file_format="html")
    assert plotly_saver.file_suffix == ".html"

    plotly_saver = PlotlyGraphSaver(file_format="json")
    assert plotly_saver.file_suffix == ".json"

    # Test default for unknown format
    plotly_saver = PlotlyGraphSaver(file_format="unknown")
    assert plotly_saver.file_suffix == ".html"


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_html(tmp_path):
    data = {"a": 1, "b": 2, "fig1": go.Figure()}

    plotly_saver = PlotlyGraphSaver(file_format="html")
    processed_data = plotly_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "fig1": "./fig1.html"}

    plotly_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "fig1.html").exists()


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_json(tmp_path):
    data = {"a": 1, "b": 2, "fig1": go.Figure()}

    plotly_saver = PlotlyGraphSaver(file_format="json")
    processed_data = plotly_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "fig1": "./fig1.json"}

    plotly_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "fig1.json").exists()


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_nested_html(tmp_path):
    data = {"a": 1, "b": 2, "figs": {"fig1": go.Figure()}}

    plotly_saver = PlotlyGraphSaver(file_format="html")
    processed_data = plotly_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "figs": {"fig1": "./figs.fig1.html"}}

    plotly_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "figs.fig1.html").exists()


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_nested_json(tmp_path):
    data = {"a": 1, "b": 2, "figs": {"fig1": go.Figure()}}

    plotly_saver = PlotlyGraphSaver(file_format="json")
    processed_data = plotly_saver.process(data)

    assert processed_data == {"a": 1, "b": 2, "figs": {"fig1": "./figs.fig1.json"}}

    plotly_saver.post_process(data_folder=tmp_path)

    assert (tmp_path / "figs.fig1.json").exists()


@pytest.mark.skipif(not module_installed("plotly"), reason="plotly not installed")
def test_plotly_saver_does_not_affect_data():
    data = {"a": 1, "b": 2, "fig1": go.Figure(), "figs": {"fig2": go.Figure()}}
    deepcopied_data = copy.deepcopy(data)

    plotly_saver = PlotlyGraphSaver(file_format="html")
    processed_data = plotly_saver.process(data)

    assert dicts_equal(data, deepcopied_data)
    assert not dicts_equal(processed_data, data)
