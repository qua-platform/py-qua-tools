import os
from pathlib import Path

import numpy as np

from qualang_tools.octave_tools import CalibrationResultPlotter


def abs_path_to(rel_path: str) -> str:
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    return os.path.join(source_dir, rel_path)

test_data = {
    "filename": "data.pkl",
    "results": {
        "image_rejection": -45,
        "lo_leakage":-36
    }
             }

def test_image_rejection():
    calibration_output = np.load(abs_path_to("iw1_cos1.npy")).tolist()
    plotter = CalibrationResultPlotter(calibration_output)
    assert plotter.get_image_rejection() == test_data["results"]["image_rejection"]

def test_lo_leakage():
    calibration_output = np.load(abs_path_to("iw1_cos1.npy")).tolist()
    plotter = CalibrationResultPlotter(calibration_output)
    assert plotter.get_image_rejection() == test_data["results"]["lo_leakage"]


