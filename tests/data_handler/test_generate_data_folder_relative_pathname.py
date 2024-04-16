from datetime import datetime
from qualang_tools.results.data_handler.data_folder_tools import generate_data_folder_relative_pathname


def test_generate_data_folder_relative_pathname():
    now = datetime(year=2023, month=2, day=1, hour=12, minute=34, second=56)
    pathname = generate_data_folder_relative_pathname(name="my_data", idx=1, created_at=now)

    assert pathname == "2023-02-01/#1_my_data_123456"
