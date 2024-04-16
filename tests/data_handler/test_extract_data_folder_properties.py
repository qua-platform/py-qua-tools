from datetime import datetime
from pathlib import Path
from qualang_tools.results.data_handler.data_folder_tools import extract_data_folder_properties


def test_extract_data_folder_properties():
    properties = extract_data_folder_properties(Path("2023-12-07/#123_test_123456"), "%Y-%m-%d/#{idx}_{name}_%H%M%S")
    expected_properties = {
        "created_at": datetime(year=2023, month=12, day=7, hour=12, minute=34, second=56),
        "path": Path("2023-12-07/#123_test_123456"),
        "idx": 123,
        "name": "test",
    }
    assert properties == expected_properties

    properties = extract_data_folder_properties(Path("2023-12-07/#124_my_test_123456"), "%Y-%m-%d/#{idx}_{name}_%H%M%S")
    expected_properties["name"] = "my_test"
    expected_properties["path"] = Path("2023-12-07/#124_my_test_123456")
    expected_properties["idx"] = 124
    assert properties == expected_properties
