from qualang_tools.results.data_handler.data_folder_tools import _validate_datetime


def test_validate_datetime_empty():
    assert not _validate_datetime("", "%Y-%m-%d")


def test_validate_datetime_empty_format():
    assert not _validate_datetime("2021-01-01", "")
    assert _validate_datetime("", "")


def test_validate_datetime_basic():
    assert _validate_datetime("2021-01-01", "%Y-%m-%d")
    assert not _validate_datetime("2021-01-01", "%Y-%m-%d %H:%M:%S")
