from pathlib import Path
import json
from typing import Dict, Any
import logging

from qm.waveform_report import WaveformReport

from .helpers import copy_nested_dict, iterate_nested_dict, update_nested_dict
from .data_processor import DataProcessor

logger = logging.getLogger(__name__)


class WaveformReportSaver(DataProcessor):
    nested_separator: str = "."

    def __init__(self):
        self.wf_reports: Dict[Path, WaveformReport] = {}
        self.samples: Dict[Path, Any] = {}

    def process(self, data):
        processed_data = copy_nested_dict(data)
        for keys, val in iterate_nested_dict(data):
            if not isinstance(val, WaveformReport):
                continue

            path = Path(self.nested_separator.join(keys) + ".json")

            wf_report = val

            self.wf_reports[path] = wf_report
            update_nested_dict(processed_data, keys, f"./{path}")

            try:
                parent_data = processed_data
                for key in keys[:-1]:
                    parent_data = parent_data[key]
                if "samples" in parent_data:
                    self.samples[path] = parent_data["samples"]
                else:
                    logger.warning(f"Waveform report in {path} did not have 'samples' key, resorting to default.")
                    pass
            except Exception:
                logger.warning(f"Could not extract waveform report samples from {path}")
                pass

        return processed_data

    def post_process(self, data_folder: Path):
        for path, wf_report in self.wf_reports.items():
            wf_json = json.dumps(wf_report.to_dict(), indent=4)
            wf_path = data_folder / path
            wf_path.write_text(wf_json)

            wf_report.job_id

            samples = self.samples[path] if path in self.samples else None
            wf_report.create_plot(samples=samples, plot=False, save_path=str(wf_path))
