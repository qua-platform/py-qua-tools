from datetime import datetime
from typing import Dict, Any, Optional
import pytest

from qualang_tools.results.data_handler.data_handler import DataHandler


def test_generate_node_contents_empty_folder(tmp_path):
    created_at = datetime(2023, 2, 1, 12, 34, 56)
    data_handler = DataHandler(root_data_folder=tmp_path, name="msmt_name")

    node_contents = data_handler.generate_node_contents(created_at=created_at)

    assert node_contents == {
        "created_at": created_at.astimezone().replace(microsecond=0).isoformat(),
        "metadata": {"name": "msmt_name", "data_path": f"2023-02-01/#1_msmt_name_123456"},
        "data": {},
        "id": 1,
        "ancestors": [],
    }


def test_generate_node_contents_with_idx_and_created_at(tmp_path):
    created_at = datetime(2023, 2, 1, 12, 34, 56)
    data_handler = DataHandler(root_data_folder=tmp_path)

    idx = 2
    node_contents = data_handler.generate_node_contents(idx=idx, created_at=created_at)

    assert node_contents == {
        "created_at": created_at.astimezone().replace(microsecond=0).isoformat(),
        "metadata": {"name": None, "data_path": f"2023-02-01/#{idx}_None_123456"},
        "data": {},
        "id": idx,
        "ancestors": [1],
    }


def test_generate_node_contents_with_all_parameters(tmp_path):
    created_at = datetime(2023, 2, 1, 12, 34, 56)
    data_handler = DataHandler(root_data_folder=tmp_path)

    idx = 2
    metadata = {"key": "value"}
    node_contents = data_handler.generate_node_contents(idx=idx, created_at=created_at, metadata=metadata)

    assert node_contents == {
        "created_at": created_at.astimezone().replace(microsecond=0).isoformat(),
        "metadata": {"name": None, "data_path": f"2023-02-01/#{idx}_None_123456", "key": "value"},
        "data": {},
        "id": idx,
        "ancestors": [1],
    }


def test_generate_node_contents_with_existing_folder_properties(tmp_path):
    now = datetime(2023, 2, 1, 12, 34, 56)
    data_handler = DataHandler(root_data_folder=tmp_path, name="msmt_name")

    # Create an empty folder with properties
    path = tmp_path / "2023-02-01" / "#1_msmt_name_123456"
    path.mkdir(parents=True)
    (path / "node.json").write_text('{"idx": 1, "created_at": "2022-01-01T00:00:00"}')

    node_contents = data_handler.generate_node_contents(created_at=now)

    assert node_contents == {
        "created_at": now.astimezone().replace(microsecond=0).isoformat(),
        "metadata": {"name": "msmt_name", "data_path": f"2023-02-01/#2_msmt_name_123456"},
        "data": {},
        "id": 2,
        "ancestors": [1],
    }
