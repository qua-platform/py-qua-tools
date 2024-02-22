import pytest
from datetime import datetime
from qualang_tools.results.data_handler.data_folder_tools import create_data_folder, DEFAULT_FOLDER_PATTERN


def test_create_data_folder(tmp_path):
    with pytest.raises(NotADirectoryError):
        create_data_folder(tmp_path / "nonexisting", name="test")


def test_create_data_folder_empty(tmp_path):
    now = datetime.now()

    properties = create_data_folder(tmp_path, name="my_test", use_datetime=now)

    path = DEFAULT_FOLDER_PATTERN.format(idx=1, name="my_test")
    path = now.strftime(path)

    properties_expected = {
        "idx": 1,
        "name": "my_test",
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "path": str(tmp_path / path),
        "relative_path": path,
    }

    assert properties == properties_expected


def test_create_successive_data_folder(tmp_path):
    now = datetime.now()

    properties = create_data_folder(tmp_path, name="my_test", use_datetime=now)
    path = DEFAULT_FOLDER_PATTERN.format(idx=1, name="my_test")
    path = now.strftime(path)

    properties_expected = {
        "idx": 1,
        "name": "my_test",
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "path": str(tmp_path / path),
        "relative_path": path,
    }

    assert properties == properties_expected

    properties = create_data_folder(tmp_path, name="my_test", use_datetime=now)

    path = DEFAULT_FOLDER_PATTERN.format(idx=2, name="my_test")
    path = now.strftime(path)

    properties_expected = {
        "idx": 2,
        "name": "my_test",
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "path": str(tmp_path / path),
        "relative_path": path,
    }

    assert properties == properties_expected