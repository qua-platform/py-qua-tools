import pytest
import importlib
import os
from qualang_tools.config.server.upload import (
    init_empty_initial_config_file,
    init_edits_file,
    init_final_config_file,
    UPLOAD_DIRECTORY
)


def test_edit_file():
    if not os.path.exists(UPLOAD_DIRECTORY):
        os.makedirs(UPLOAD_DIRECTORY)
    init_empty_initial_config_file()
    init_edits_file()
    init_final_config_file()

    assert os.path.isdir(UPLOAD_DIRECTORY)
    assert os.path.exists(os.path.join(UPLOAD_DIRECTORY, "config_edits.py"))

    import config_edits
    import config_final

    importlib.reload(config_edits)
    importlib.reload(config_final)
    configuration = config_final.configuration
    assert "version" in configuration
    assert configuration["version"] >= 0
