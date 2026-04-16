import numpy as np

from qm.qua import program, declare_with_stream, assign, fixed
from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange

from tests.tests_qua_utilities.fetch_xarray_helpers import (
    shots, frequencies, amp_start, amp_stop, amp_step, amp_values, qubits,
    make_product, simulate_and_fetch, assert_dims_and_shape, assert_allclose_sel,
)


def test_single_save(qmm):
    prod = make_product()
    with program() as prog:
        for args in prod:
            single_save = declare_with_stream(int, "shot_st")
            single_save_avg = declare_with_stream(float, "shot_avg_st", average_axes=["shot"])
            assign(single_save, args.shot)
            assign(single_save_avg, args.frequency * args.amp)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "shot_st", ("shot", "qubit", "frequency", "amp"), (shots, len(qubits), len(frequencies), len(amp_values)))
    assert_dims_and_shape(xarray_data, "shot_avg_st", ("qubit", "frequency", "amp"), (len(qubits), len(frequencies), len(amp_values)))

    for i in range(shots):
        assert (xarray_data["shot_st"][i] == i).all(), f"shot_st[{i}]: expected all values to be {i}, got {xarray_data['shot_st'][i].values}"

    for f in frequencies:
        for a in amp_values:
            assert_allclose_sel(xarray_data, "shot_avg_st", a * f, frequency=f, amp=a)


def test_no_native_iterables(qmm):
    """Only qua iterables — exercises the no-native-columns branch."""
    n_shots = 10
    prod = QuaProduct([
        QuaIterableRange("shot", n_shots),
        QuaIterable("frequency", frequencies),
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(int, "shot_st")
            assign(s, args.shot)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "shot_st", ("shot", "frequency"), (n_shots, len(frequencies)))

    for i in range(n_shots):
        assert (xarray_data["shot_st"][i] == i).all(), f"shot_st[{i}]: expected all values to be {i}, got {xarray_data['shot_st'][i].values}"


def test_no_qua_iterables(qmm):
    """Only native iterables — non_native_shape is empty."""
    prod = QuaProduct([
        NativeIterable("qubit", qubits),
        NativeIterableRange("amp", amp_start, amp_stop, amp_step),
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(fixed, "amp_st")
            assign(s, args.amp)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "amp_st", ("qubit", "amp"), (len(qubits), len(amp_values)))

    for a in amp_values:
        assert_allclose_sel(xarray_data, "amp_st", a, amp=a)

    for q in qubits:
        for a in amp_values:
            assert_allclose_sel(xarray_data, "amp_st", a, qubit=q, amp=a)


def test_pass_as_list(qmm):
    """Pass sweep as a list of iterables instead of QuaProduct."""
    sweep_list = [
        QuaIterableRange("shot", 10),
        NativeIterable("qubit", qubits),
        QuaIterable("frequency", frequencies),
    ]
    prod = QuaProduct(sweep_list)
    with program() as prog:
        for args in prod:
            s = declare_with_stream(int, "shot_st")
            assign(s, args.shot)

    xarray_data = simulate_and_fetch(qmm, prog, sweep_list)

    assert_dims_and_shape(xarray_data, "shot_st", ("shot", "qubit", "frequency"), (10, len(qubits), len(frequencies)))

    for i in range(10):
        assert (xarray_data["shot_st"][i] == i).all(), f"shot_st[{i}]: expected all values to be {i}, got {xarray_data['shot_st'][i].values}"


def test_interleaved_dim_ordering(qmm):
    """Interleaved native/qua iterables to verify transpose permutation correctness."""
    n_shots = 10
    prod = QuaProduct([
        QuaIterableRange("shot", n_shots),
        NativeIterable("qubit", qubits),
        QuaIterable("frequency", frequencies),
        NativeIterableRange("amp", amp_start, amp_stop, amp_step),
    ])
    with program() as prog:
        for args in prod:
            s_shot = declare_with_stream(int, "shot_st")
            s_freq = declare_with_stream(fixed, "freq_st")
            assign(s_shot, args.shot)
            assign(s_freq, args.frequency)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "shot_st", ("shot", "qubit", "frequency", "amp"), (n_shots, len(qubits), len(frequencies), len(amp_values)))
    assert_dims_and_shape(xarray_data, "freq_st", ("shot", "qubit", "frequency", "amp"), (n_shots, len(qubits), len(frequencies), len(amp_values)))

    for i in range(n_shots):
        assert (xarray_data["shot_st"][i] == i).all(), f"shot_st[{i}]: expected all values to be {i}, got {xarray_data['shot_st'][i].values}"

    for f in frequencies:
        assert_allclose_sel(xarray_data, "freq_st", f, frequency=f)


def test_coordinate_values(qmm):
    """Verify that xarray coordinate values match the original iterable values."""
    prod = make_product()
    with program() as prog:
        for args in prod:
            s = declare_with_stream(int, "shot_st")
            assign(s, args.shot)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert np.array_equal(xarray_data.coords["shot"].values, np.arange(shots)), f"shot coords: expected {np.arange(shots)}, got {xarray_data.coords['shot'].values}"
    assert np.array_equal(xarray_data.coords["qubit"].values, qubits), f"qubit coords: expected {qubits}, got {xarray_data.coords['qubit'].values}"
    assert np.allclose(xarray_data.coords["frequency"].values, frequencies), f"frequency coords: expected {frequencies}, got {xarray_data.coords['frequency'].values}"
    assert np.allclose(xarray_data.coords["amp"].values, amp_values), f"amp coords: expected {amp_values}, got {xarray_data.coords['amp'].values}"
