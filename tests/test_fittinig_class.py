import numpy as np
import pytest

from qualang_tools.plot.fitting import Fit

@pytest.mark.parametrize("a", [5, 10, -1])
@pytest.mark.parametrize("b", [1, 11, 0])
def test_linear(a, b):

    fit = Fit()
    x = np.linspace(0, 100, 100)
    y = a * x + b
    out = fit.linear(x_data=x, y_data=y)

    np.testing.assert_allclose(out['fit_func'](x), y, rtol=1e-5, atol=1e-5)

@pytest.mark.parametrize("amp", [0.2, 0.3, 0.4])
@pytest.mark.parametrize("T1", [10, 50, 100])
@pytest.mark.parametrize("final_offset", [0.05, 0.1, 0.2])
def test_T1(amp, T1, final_offset):
    fit = Fit()
    x = np.linspace(0, 100, 100)
    y = amp * np.exp(-x * (1/T1)) + final_offset
    out = fit.T1(x_data=x, y_data=y)

    np.testing.assert_allclose(out['fit_func'](x), y, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("final_offset", [0.01, 0.05])
@pytest.mark.parametrize("T2", [100, 200])
@pytest.mark.parametrize("amp", [1, 2])
@pytest.mark.parametrize("initial_offset", [0, 0.01])
@pytest.mark.parametrize("f", [10e-3, 15e-3])
@pytest.mark.parametrize("phase", [0, 0.01])
def test_ramsey(final_offset, T2, amp, initial_offset, f, phase):
    fit = Fit()
    tau_min = 32
    tau_max = 800
    d_tau = 16
    x = np.arange(tau_min, tau_max + 0.1, d_tau)
    y = final_offset * (1 - np.exp(-x * (1/T2))) + amp / 2 * (
            np.exp(-x * (1/T2))
            * (initial_offset * 2 + np.cos(2 * np.pi * f * x + phase))
            )
    out = fit.ramsey(x_data=x, y_data=y)

    np.testing.assert_allclose(out['fit_func'](x), y, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("kc", [3, 5])
@pytest.mark.parametrize("k", [10, 15])
@pytest.mark.parametrize("f", [10, 50])
@pytest.mark.parametrize("offset", [0.01, 0.15, 0.2])
def test_transmission_resonator_spectroscopy(kc, k, f, offset):
    fit = Fit()
    x = np.linspace(0, 100, 100)
    y = ((kc/k) / (1 + (4 * ((x - f) ** 2) / (k ** 2)))) + offset
    out = fit.transmission_resonator_spectroscopy(x_data=x, y_data=y)

    np.testing.assert_allclose(out['fit_func'](x), y, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("kc", [3, 5])
@pytest.mark.parametrize("k", [10, 15])
@pytest.mark.parametrize("f", [10, 50])
@pytest.mark.parametrize("offset", [0.1, 0.15])
@pytest.mark.parametrize("slope", [0.0001, 0.0002])
def test_reflection_resonator_spectroscopy(kc, k, f, offset, slope):
    fit = Fit()
    x = np.linspace(0, 100, 100)
    y = offset-((kc/k) / (1 + (4 * ((x - f) ** 2) / (k ** 2)))) + slope * x
    out = fit.reflection_resonator_spectroscopy(x_data=x, y_data=y)

    np.testing.assert_allclose(out['fit_func'](x), y, rtol=1e-5, atol=1e-5)


@pytest.mark.parametrize("offset", [0.01, 0.05])
@pytest.mark.parametrize("T", [2000, 2500])
@pytest.mark.parametrize("amp", [0.3, 0.5])
@pytest.mark.parametrize("f", [20e-4, 25e-4])
@pytest.mark.parametrize("phase", [0, 0.01])
def test_rabi(offset, T, amp, f, phase):
    fit = Fit()
    tau_min = 32
    tau_max = 800
    d_tau = 16
    x = np.arange(tau_min, tau_max + 0.1, d_tau)
    y = amp * (np.sin(0.5 * (2 * np.pi * f) * x + phase))**2 * np.exp(-x / T) + offset

    out = fit.rabi(x_data=x, y_data=y)

    np.testing.assert_allclose(out['fit_func'](x), y, rtol=1e-5, atol=1e-5)