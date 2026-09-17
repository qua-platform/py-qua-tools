from unittest.mock import MagicMock

import numpy as np
from qm import SimulatorControllerSamples

from qualang_tools.results.data_handler.data_processors import SimulatorControllerSamplesSaver


def test_simulator_controller_samples_saver_serialises_analog_and_digital():
    samples = MagicMock(spec=SimulatorControllerSamples)
    samples.analog = {"1": np.array([0.1, 0.2])}
    samples.digital = {"1": np.array([0, 1])}
    samples.analog_sampling_rate = {"1": 1e9}

    data = {"sim": samples, "keep": "ok"}
    processed = SimulatorControllerSamplesSaver().process(data)

    assert processed["keep"] == "ok"
    assert list(processed["sim"]["analog"].keys()) == ["1"]
    np.testing.assert_array_equal(processed["sim"]["analog"]["1"], np.array([0.1, 0.2]))
    np.testing.assert_array_equal(processed["sim"]["digital"]["1"], np.array([0, 1]))
    assert processed["sim"]["analog_sampling_rate"]["1"] == 1e9


def test_simulator_controller_samples_saver_ignores_other_types():
    data = {"x": 3}
    processed = SimulatorControllerSamplesSaver().process(data)
    assert processed == {"x": 3}
