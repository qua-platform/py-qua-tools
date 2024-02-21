import pytest
from pathlib import Path
from qualang_tools.results.data_handler.data_folder_tools import extract_data_folder_properties


def test_extract_data_folder_properties():
    properties = extract_data_folder_properties(Path("#123_test_123456"), "#{idx}_{name}_%H%M%S")
    expected_properties = {
        "idx": 123,
        "name": "test",
        "hour": 12,
        "minute": 34,
        "second": 56,
        "path": "#123_test_123456",
    }
    assert properties == expected_properties

    properties = extract_data_folder_properties(Path("#123_my_test_123456"), "#{idx}_{name}_%H%M%S")
    expected_properties["name"] = "my_test"
    expected_properties["path"] = "#123_my_test_123456"
    assert properties == expected_properties
