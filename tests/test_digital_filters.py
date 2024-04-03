import pytest
import numpy as np
from qualang_tools.digital_filters import *


@pytest.mark.parametrize("low_pass_exp", [
     [500, -0.25, 200],
     [500, 0.25, 200],
])
def test_exponential_decay(low_pass_exp):
    t_max = low_pass_exp[0]
    A = low_pass_exp[1]
    tau = low_pass_exp[2]
    t = np.arange(0, t_max, 1)
    assert np.all(exponential_decay(t, A, tau) == 1 + A * np.exp(-t/tau))

@pytest.mark.parametrize("high_pass_exp", [
     [500, 200],
])
def test_high_pass_exponential(high_pass_exp):
    t_max = high_pass_exp[0]
    tau = high_pass_exp[1]
    t = np.arange(0, t_max, 1)
    assert np.all(high_pass_exponential(t, tau) == np.exp(-t/tau))


@pytest.mark.parametrize("single_exp_correction", [
     [-0.25, 200, 1],
     [0.25, 200, 1],
     [0.25, 200, 2],
     [-0.01, 2000, 1],
])
def test_single_exp_correction(single_exp_correction):
    A = single_exp_correction[0]
    tau = single_exp_correction[1]
    ts = single_exp_correction[2]
    feedforward, feedback = single_exponential_correction(A, tau, ts)
    feedforward = np.array(feedforward)
    print(f"\nfeedback: {feedback}")
    print(f"feedforward: {feedforward}")
    assert -1 < feedback[0] < 1  # Must be within (-1, 1)
    assert 0 <= feedback[0]  # Low pass correction must be > 0
    assert np.all(-2 < np.array(feedforward))  # Must be within (-2, 2)
    assert np.all(np.array(feedforward) < 2)  # Must be within (-2, 2)
    assert np.all(feedforward == single_exponential_correction(A, tau*2, 2*ts)[0])
    assert feedback == single_exponential_correction(A, tau*2, 2*ts)[1]


@pytest.mark.parametrize("hp_correction", [
     [20000, 1],
     [2000000, 2],
     [10, 1],
])
def test_hp_correction(hp_correction):
    tau = hp_correction[0]
    ts = hp_correction[1]
    feedforward, feedback = highpass_correction(tau, ts)
    print(f"\nfeedback: {feedback}")
    print(f"feedforward: {feedforward}")
    assert -1 < feedback[0] < 1  # Must be within (-1, 1)
    assert 0 <= feedback[0]  # High pass correction must be > 0
    assert np.all(-2 < np.array(feedforward))  # Must be within (-2, 2)
    assert np.all(np.array(feedforward) < 2)  # Must be within (-2, 2)
    assert np.all(feedforward == highpass_correction(tau/2, 2*ts)[0])
    assert feedback == highpass_correction(tau/2, 2*ts)[1]

@pytest.mark.parametrize("calc_correction", [
     [[(0.25, 200)], None, 1],
     [[(-0.25, 200)], None, 1],
     [[(-0.25, 200)], None, 2],
     [None, [20_000], 1],
     [None, [20_000], 2],
])
def test_single_calc_filter_taps(calc_correction):
    low_pass = calc_correction[0]
    high_pass = calc_correction[1]
    ts = calc_correction[2]
    feedforward, feedback = calc_filter_taps(fir=None, exponential=low_pass, highpass=high_pass, bounce=None, delay=None, Ts=ts)
    print(f"\nfeedback: {feedback}")
    print(f"feedforward: {feedforward}")
    if low_pass is None:
        assert np.all(feedforward == highpass_correction(high_pass[0], ts)[0])
        assert feedback[0] == highpass_correction(high_pass[0], ts)[1]
    elif high_pass is None:
        assert np.all(feedforward == single_exponential_correction(low_pass[0][0], low_pass[0][1], ts)[0])
        assert feedback[0] == single_exponential_correction(low_pass[0][0], low_pass[0][1], ts)[1]


@pytest.mark.parametrize("static_calc_correction", [
     [[(-0.25, 200)], None, 1, [[1.3322259136212624, -1.325581395348837], [0.9933554817275746]]],
     [None, [20_000], 1, [[1.000025, -0.999975], [0.9999990463225004]]],
])
def test_single_calc_filter_taps_static(static_calc_correction):
    low_pass = static_calc_correction[0]
    high_pass = static_calc_correction[1]
    ts = static_calc_correction[2]
    static_values = static_calc_correction[3]
    feedforward, feedback = calc_filter_taps(fir=None, exponential=low_pass, highpass=high_pass, bounce=None, delay=None, Ts=ts)
    print(f"\nfeedback: {feedback}")
    print(f"feedforward: {feedforward}")
    assert np.all(feedforward == static_values[0])
    assert feedback[0] == static_values[1][0]

