import pytest
from datetime import datetime

from qualang_tools.results.data_handler import *


def test_determine_data_folder_nonextisting(tmp_path):
    with pytest.raises(NotADirectoryError):
        determine_data_folder(root_data_folder=tmp_path / "nonexisting", name="test")


def test_determine_data_folder_default_structure(tmp_path):
    date_time = datetime.now()
    data_folder = determine_data_folder(root_data_folder=tmp_path, name="test", idx=123)

    assert data_folder == tmp_path / date_time.strftime("%Y-%m-%d") / f"#123_test_{date_time.strftime('%H%M%S')}"
