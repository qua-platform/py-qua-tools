from unittest.mock import MagicMock

import pytest

from qualang_tools.results.results import fetching_tool, progress_counter, wait_until_job_is_paused


def test_fetching_tool_empty_data_list_raises():
    with pytest.raises(Exception, match="empty"):
        fetching_tool(MagicMock(), [])


def test_fetching_tool_invalid_mode_raises():
    with pytest.raises(Exception, match="not supported"):
        fetching_tool(MagicMock(), ["I"], mode="nope")


def test_fetching_tool_wait_for_all_fetch_all():
    handles = MagicMock()
    handles.fetch_results.return_value = {"I": [1], "Q": [2]}
    job = MagicMock()
    job.result_handles = handles

    tool = fetching_tool(job, ["I", "Q"], mode="wait_for_all")
    I, Q = tool.fetch_all()

    handles.fetch_results.assert_called_once_with(wait_until_done=True, stream_names=["I", "Q"])
    assert I == [1]
    assert Q == [2]


def test_fetching_tool_live_missing_stream_raises_warning():
    handles = MagicMock(spec=["fetch_results", "get", "is_processing"])
    job = MagicMock()
    job.result_handles = handles
    with pytest.raises(Warning, match="not saved"):
        fetching_tool(job, ["I"], mode="live")


def test_fetching_tool_is_processing_true_then_once_more():
    handles = MagicMock()
    handles.is_processing.side_effect = [True, False, False]
    handles.I = MagicMock()
    handles.get.return_value = MagicMock()
    job = MagicMock()
    job.result_handles = handles

    tool = fetching_tool(job, ["I"], mode="live")
    assert tool.is_processing() is True
    assert tool.is_processing() is True
    assert tool.is_processing() is False


def test_progress_counter_prints(capsys):
    progress_counter(0, 4, progress_bar=True, percent=True)
    out = capsys.readouterr().out
    assert "Progress:" in out
    assert "25.0%" in out


def test_wait_until_job_is_paused_returns_when_paused():
    job = MagicMock()
    job.is_paused.return_value = True
    assert wait_until_job_is_paused(job, timeout=1) is True


def test_wait_until_job_is_paused_strict_timeout():
    job = MagicMock()
    job.is_paused.return_value = False
    with pytest.raises(TimeoutError, match="Timeout"):
        wait_until_job_is_paused(job, timeout=0.2, strict_timeout=True)
