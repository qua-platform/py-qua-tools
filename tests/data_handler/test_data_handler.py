import json
import pytest
from datetime import datetime

from qualang_tools.results.data_handler.data_folder_tools import DEFAULT_FOLDER_PATTERN
from qualang_tools.results.data_handler.data_handler import DataHandler
from qualang_tools.results.data_handler.data_processors import DataProcessor


def test_data_handler_basic(tmp_path):
    data_handler = DataHandler(root_data_folder=tmp_path)

    data = {"a": 1, "b": 2, "c": 3}

    now = datetime.now()

    data_handler.save_data(data, "my_data", use_datetime=now)

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder / "data.json").exists()

    file_data = json.loads((tmp_path / expected_data_folder / "data.json").read_text())
    assert file_data == data


def test_data_handler_metadata(tmp_path):
    data_handler = DataHandler(root_data_folder=tmp_path)

    data = {"a": 1, "b": 2, "c": 3}

    metadata = {"meta": "data"}

    now = datetime.now()

    data_handler.save_data(data, "my_data", metadata=metadata, use_datetime=now)

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder / "data.json").exists()
    assert (tmp_path / expected_data_folder / "metadata.json").exists()

    file_data = json.loads((tmp_path / expected_data_folder / "data.json").read_text())
    file_metadata = json.loads(
        (tmp_path / expected_data_folder / "metadata.json").read_text()
    )

    assert file_data == data
    assert file_metadata == metadata


def test_data_handler_custom_processors(tmp_path):
    class TestProcessor(DataProcessor):
        def process(self, data):
            data["a"] = 42
            return data

    data_handler = DataHandler(
        root_data_folder=tmp_path, data_processors=[TestProcessor()]
    )

    data = {"a": 1, "b": 2, "c": 3}

    now = datetime.now()

    data_handler.save_data(data, "my_data", use_datetime=now)

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder / "data.json").exists()

    file_data = json.loads((tmp_path / expected_data_folder / "data.json").read_text())
    assert file_data == {"a": 42, "b": 2, "c": 3}


def test_data_handler_matplotlib_processor(tmp_path):
    data_handler = DataHandler(root_data_folder=tmp_path)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [1, 2, 3])

    data = {"a": 1, "b": 2, "c": 3, "my_fig": fig}

    now = datetime.now()

    data_handler.save_data(data, "my_data", use_datetime=now)

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder / "data.json").exists()

    file_data = json.loads((tmp_path / expected_data_folder / "data.json").read_text())

    assert file_data == {"a": 1, "b": 2, "c": 3, "my_fig": "./my_fig.png"}

    assert (tmp_path / expected_data_folder / "my_fig.png").exists()


def test_data_handler_no_name_create_folder(tmp_path):
    data_handler = DataHandler(root_data_folder=tmp_path)
    assert data_handler.name is None

    now = datetime.now()

    with pytest.raises(ValueError):
        data_handler.create_data_folder(use_datetime=now)


def test_data_handler_initialized_name_create_folder(tmp_path):
    data_handler = DataHandler(name="my_data", root_data_folder=tmp_path)
    assert data_handler.name == "my_data"

    now = datetime.now()

    data_handler.create_data_folder(use_datetime=now)

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder).exists()


def test_data_handler_overwrite_initialized_name_create_folder(tmp_path):
    data_handler = DataHandler(name="my_data", root_data_folder=tmp_path)
    assert data_handler.name == "my_data"

    now = datetime.now()

    data_handler.create_data_folder(name="my_new_data", use_datetime=now)
    assert data_handler.name == "my_new_data"

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_new_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder).exists()


def test_data_handler_no_name_save_data(tmp_path):
    data_handler = DataHandler(root_data_folder=tmp_path)
    assert data_handler.name is None

    with pytest.raises(ValueError):
        data_handler.save_data({"a": 1, "b": 2, "c": 3})


def test_data_handler_initialized_name_save_data(tmp_path):
    data_handler = DataHandler(name="my_data", root_data_folder=tmp_path)
    assert data_handler.name == "my_data"

    now = datetime.now()

    data_handler.save_data({"a": 1, "b": 2, "c": 3}, use_datetime=now)

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder / "data.json").exists()


def test_data_handler_overwrite_initialized_name_save_data(tmp_path):
    data_handler = DataHandler(name="my_data", root_data_folder=tmp_path)
    assert data_handler.name == "my_data"

    now = datetime.now()

    data_handler.save_data(
        {"a": 1, "b": 2, "c": 3}, name="my_new_data", use_datetime=now
    )
    assert data_handler.name == "my_new_data"

    expected_data_folder = DEFAULT_FOLDER_PATTERN.format(name="my_new_data", idx=1)
    expected_data_folder = now.strftime(expected_data_folder)

    assert (tmp_path / expected_data_folder / "data.json").exists()
