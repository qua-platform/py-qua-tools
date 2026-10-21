from types import SimpleNamespace
from unittest.mock import MagicMock

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pytest

from qualang_tools.plot.plot import (
    get_simulated_samples_by_element,
    interrupt_on_close,
    plot_demodulated_data_1d,
    plot_demodulated_data_2d,
)


def test_plot_demodulated_data_1d_returns_figure():
    x = np.linspace(0, 1, 20)
    I = np.ones(20)
    Q = np.zeros(20)
    fig = plot_demodulated_data_1d(x, I, Q, x_label="x", title="t", amp_and_phase=False)
    if isinstance(fig, tuple):
        fig = fig[0]
    assert fig is not None
    assert len(fig.axes) == 2
    plt.close(fig)


def test_plot_demodulated_data_2d_returns_figure():
    x = np.linspace(0, 1, 5)
    y = np.linspace(0, 1, 4)
    I = np.ones((4, 5))
    Q = np.zeros((4, 5))
    fig = plot_demodulated_data_2d(x, y, I, Q, x_label="x", y_label="y", title="t", amp_and_phase=False)
    assert fig is not None
    plt.close(fig)


def test_plot_demodulated_data_1d_invalid_plot_option():
    x = np.linspace(0, 1, 5)
    with pytest.raises(ValueError, match="doesn't exists"):
        plot_demodulated_data_1d(x, x, x, plot_options={"not_a_key": 1})


def test_interrupt_on_close_registers_callback():
    fig = plt.figure()
    job = MagicMock()
    interrupt_on_close(fig, job)
    fig.canvas.callbacks.process("close_event", MagicMock(canvas=fig.canvas))
    job.halt.assert_called_once()
    plt.close(fig)


def test_get_simulated_samples_by_element_single_input():
    analog = np.arange(10, dtype=float)
    digital = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    controller = SimpleNamespace(analog={"1": analog}, digital={"1": digital})
    samples = SimpleNamespace(con1=controller)
    job = MagicMock()
    job.get_simulated_samples.return_value = samples

    config = {
        "elements": {
            "qe1": {
                "singleInput": {"port": ("con1", 1)},
                "digitalInputs": {"d": {"port": ("con1", 1)}},
            }
        }
    }
    analog_samples, digital_samples = get_simulated_samples_by_element("qe1", job, config)
    np.testing.assert_array_equal(analog_samples, analog)
    np.testing.assert_array_equal(digital_samples[0], digital.astype(int))
    job.result_handles.wait_for_all_values.assert_called_once()
