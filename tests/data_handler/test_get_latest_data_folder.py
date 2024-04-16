from datetime import datetime
from pathlib import Path
from qualang_tools.results.data_handler.data_folder_tools import (
    get_latest_data_folder,
    create_data_folder,
    DEFAULT_FOLDER_PATTERN,
)


def test_get_latest_data_folder_empty(tmp_path):
    assert get_latest_data_folder(tmp_path) is None


def test_get_latest_data_folder_default_structure(tmp_path):
    date_folder = tmp_path / "2021-01-05"
    date_folder.mkdir()
    (date_folder / "#123_test_123456").mkdir()

    properties = get_latest_data_folder(tmp_path)
    expected_properties = {
        "idx": 123,
        "name": "test",
        "created_at": datetime(year=2021, month=1, day=5, hour=12, minute=34, second=56),
        "path": date_folder / "#123_test_123456",
        "relative_path": Path(f"{date_folder.name}/#123_test_123456"),
    }

    assert properties == expected_properties


def test_get_latest_data_folder_two_items(tmp_path):
    date_folder = tmp_path / "2021-01-05"
    date_folder.mkdir()
    (date_folder / "#123_test_123456").mkdir()
    (date_folder / "#124_test_123457").mkdir()

    properties = get_latest_data_folder(tmp_path)
    expected_properties = {
        "idx": 124,
        "name": "test",
        "created_at": datetime(year=2021, month=1, day=5, hour=12, minute=34, second=57),
        "path": date_folder / "#124_test_123457",
        "relative_path": Path(f"{date_folder.name}/#124_test_123457"),
    }

    assert properties == expected_properties


def test_get_latest_data_folder_two_items_different_date(tmp_path):
    date_folder = tmp_path / "2021-01-05"
    date_folder.mkdir()
    (date_folder / "#123_test_123456").mkdir()

    date_folder = tmp_path / "2021-01-06"
    date_folder.mkdir()
    (date_folder / "#124_test_123457").mkdir()

    properties = get_latest_data_folder(tmp_path)
    expected_properties = {
        "idx": 124,
        "name": "test",
        "created_at": datetime(year=2021, month=1, day=6, hour=12, minute=34, second=57),
        "path": date_folder / "#124_test_123457",
        "relative_path": Path(f"{date_folder.name}/#124_test_123457"),
    }

    assert properties == expected_properties


def test_get_latest_data_folder_different_date_empty_last_folder(tmp_path):
    date_folder = tmp_path / "2021-01-05"
    date_folder.mkdir()
    (date_folder / "#123_test_123456").mkdir()

    date_folder = tmp_path / "2021-01-06"
    date_folder.mkdir()

    properties = get_latest_data_folder(tmp_path)
    expected_properties = {
        "idx": 123,
        "name": "test",
        "created_at": datetime(year=2021, month=1, day=5, hour=12, minute=34, second=56),
        "path": tmp_path / "2021-01-05/#123_test_123456",
        "relative_path": Path("2021-01-05/#123_test_123456"),
    }

    assert properties == expected_properties


def test_get_latest_data_folder_switched_idxs(tmp_path):
    date_folder = tmp_path / "2021-01-05"
    (date_folder / "#124_test_123456").mkdir(parents=True)

    date_folder = tmp_path / "2021-01-06"
    (date_folder / "#123_test_123457").mkdir(parents=True)

    properties = get_latest_data_folder(tmp_path)
    expected_properties = {
        "idx": 123,
        "name": "test",
        "created_at": datetime(year=2021, month=1, day=6, hour=12, minute=34, second=57),
        "path": date_folder / "#123_test_123457",
        "relative_path": Path(f"{date_folder.name}/#123_test_123457"),
    }

    assert properties == expected_properties


def test_get_latest_data_folder_correct_order(tmp_path):
    from qualang_tools.results.data_handler.data_folder_tools import (
        get_latest_data_folder,
    )

    now = datetime.now()

    for idx in range(1, 105):
        path = DEFAULT_FOLDER_PATTERN.format(idx=idx, name="my_test")
        path = now.strftime(path)
        (tmp_path / path).mkdir(parents=True)

        properties_latest = get_latest_data_folder(tmp_path)

        assert properties_latest["idx"] == idx
