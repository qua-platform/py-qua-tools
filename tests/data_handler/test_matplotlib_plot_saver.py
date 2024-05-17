import pytest
import json

from qualang_tools.results.data_handler.data_handler import save_data
from qualang_tools.results.data_handler.data_processors import MatplotlibPlotSaver


@pytest.fixture
def fig():
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])
    return fig


def test_matplotlib_plot_saver_process(fig):
    matplotlib_plot_saver = MatplotlibPlotSaver()
    data = {"a": 1, "b": 2, "c": fig}
    data = matplotlib_plot_saver.process(data)

    assert data == {"a": 1, "b": 2, "c": "./c.png"}


def test_save_plot_basic(tmp_path, fig):
    data = {"a": 1, "b": 2, "c": fig}

    with pytest.raises(TypeError):
        save_data(data_folder=tmp_path, data=data)

    assert len(list(tmp_path.iterdir())) == 0

    save_data(data_folder=tmp_path, data=data, node_contents={}, data_processors=[MatplotlibPlotSaver()])

    assert set(f.name for f in tmp_path.iterdir()) == set(["data.json", "node.json", "c.png"])

    file_data = json.loads((tmp_path / "data.json").read_text())

    assert file_data == {"a": 1, "b": 2, "c": "./c.png"}


def test_matplotlib_nested_save(tmp_path, fig):
    data = {"q0": {"fig": fig, "value": 42}}

    save_data(data_folder=tmp_path, data=data, node_contents={}, data_processors=[MatplotlibPlotSaver()])

    assert set(f.name for f in tmp_path.iterdir()) == set(["data.json", "node.json", "q0.fig.png"])

    file_data = json.loads((tmp_path / "data.json").read_text())
    assert file_data == {"q0": {"fig": "./q0.fig.png", "value": 42}}
