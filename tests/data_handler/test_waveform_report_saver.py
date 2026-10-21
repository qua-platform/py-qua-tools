from pathlib import Path
from unittest.mock import MagicMock

from qm.waveform_report import WaveformReport

from qualang_tools.results.data_handler.data_processors import WaveformReportSaver


def test_waveform_report_saver_rewrites_nested_path():
    report = MagicMock(spec=WaveformReport)
    data = {"nested": {"wf": report, "samples": {"analog": {}}}}

    saver = WaveformReportSaver()
    processed = saver.process(data)

    assert processed["nested"]["wf"] == "./nested.wf.json"
    assert list(saver.wf_reports.keys()) == [Path("nested.wf.json")]
    assert Path("nested.wf.json") in saver.samples


def test_waveform_report_saver_without_samples_keeps_other_data():
    report = MagicMock(spec=WaveformReport)
    data = {"wf": report, "other": 1}

    saver = WaveformReportSaver()
    processed = saver.process(data)

    assert processed["wf"] == "./wf.json"
    assert processed["other"] == 1
