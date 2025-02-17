import os
import pickle
from pathlib import Path

import numpy as np
from qualang_tools.octave_tools import CalibrationResultPlotter
import matplotlib.pyplot as plt


def abs_path_to(rel_path: str) -> str:
    source_path = Path(__file__).resolve()
    source_dir = source_path.parent
    return os.path.join(source_dir, rel_path)


test_data = {
    "filename": "calib_res.pkl",
    "results": {
        "image_rejection": -42.27341113038968,
        "lo_leakage": -27.22687176440225,
        "image_zero_handling": [(16, 17)],
        "voltages_to_dbm": np.array([1, 2, 3]),
        "integration_length": 10_000,
    },
}


def open_test_data():
    with open(abs_path_to(test_data["filename"]), "rb") as file:
        return pickle.load(file)


def test_image_rejection():
    calibration_output = open_test_data()
    plotter = CalibrationResultPlotter(calibration_output)
    assert plotter.get_image_rejection() == test_data["results"]["image_rejection"]


def test_lo_leakage():
    calibration_output = open_test_data()
    plotter = CalibrationResultPlotter(calibration_output)
    print(plotter.get_lo_leakage_rejection())
    assert plotter.get_lo_leakage_rejection() == test_data["results"]["lo_leakage"]


def test_zero_handling():
    calibration_output = open_test_data()
    plotter = CalibrationResultPlotter(calibration_output)
    data = plotter.if_data[plotter.if_frequency].fine.image
    assert plotter._handle_zero_indices_and_masking(data) == test_data["results"]["image_zero_handling"]


def test_show_lo_leakage_calibration_result():
    calibration_output = open_test_data()
    plotter = CalibrationResultPlotter(calibration_output)
    plotter.show_lo_leakage_calibration_result()
    plt.close()


def test_show_image_rejection_calibration_result():
    calibration_output = open_test_data()
    plotter = CalibrationResultPlotter(calibration_output)
    plotter.show_image_rejection_calibration_result()
    plt.close()


def test_convert_to_dbm():
    volts = test_data["results"]["voltages_to_dbm"]
    expected_dbm = 10 * np.log10(volts / (50 * 2) * 1000)
    result = CalibrationResultPlotter._convert_to_dbm(volts)
    np.testing.assert_array_almost_equal(result, expected_dbm)

def test_integration_length():
    assert CalibrationResultPlotter._get_integration_length() == test_data["results"]["integration_length"]


