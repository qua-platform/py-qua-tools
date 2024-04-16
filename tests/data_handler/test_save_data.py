import json
from qualang_tools.results.data_handler.data_handler import save_data


def test_save_data_basic(tmp_path):
    data = {"a": 1, "b": 2, "c": 3}
    save_data(data_folder=tmp_path, data=data, node_contents={})

    assert set(f.name for f in tmp_path.iterdir()) == set(["data.json", "node.json"])

    file_data = json.loads((tmp_path / "data.json").read_text())

    assert file_data == data


def test_save_data_metadata(tmp_path):
    data = {"a": 1, "b": 2, "c": 3}
    metadata = {"meta": "data"}
    save_data(data_folder=tmp_path, data=data, metadata=metadata, node_contents={})
    assert set(f.name for f in tmp_path.iterdir()) == set(["data.json", "node.json"])

    file_data = json.loads((tmp_path / "data.json").read_text())
    file_node = json.loads((tmp_path / "node.json").read_text())

    assert file_data == data
    assert file_node == {"metadata": metadata}
