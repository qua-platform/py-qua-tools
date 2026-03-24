import numpy as np

from qm.qua import program, declare_with_stream, assign, fixed
from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange

from qualang_tools.loops.qua_iterable_postprocess import fetch_xarray_data
from tests.tests_qua_utilities.conftest import config
from tests.tests_qua_utilities.fetch_xarray_helpers import (
    simulation_config, shots, frequencies, amp_start, amp_stop, amp_step, amp_values, qubits, make_product,
)


def test_single_save(qmm):
    prod = make_product()
    with program() as prog:
        for args in prod:
            single_save = declare_with_stream(int, "shot_st")
            single_save_avg = declare_with_stream(float, "shot_avg_st", average_axes=["shot"])
            assign(single_save, args.shot)
            assign(single_save_avg, args.frequency * args.amp)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["shot_st"].dims == ("shot", "qubit", "frequency", "amp"), f"shot_st dims: expected ('shot', 'qubit', 'frequency', 'amp'), got {xarray_data['shot_st'].dims}"
    assert xarray_data["shot_st"].shape == (shots, len(qubits), len(frequencies), len(amp_values)), f"shot_st shape: expected {(shots, len(qubits), len(frequencies), len(amp_values))}, got {xarray_data['shot_st'].shape}"

    assert xarray_data["shot_avg_st"].dims == ("qubit", "frequency", "amp"), f"shot_avg_st dims: expected ('qubit', 'frequency', 'amp'), got {xarray_data['shot_avg_st'].dims}"
    assert xarray_data["shot_avg_st"].shape == (len(qubits), len(frequencies), len(amp_values)), f"shot_avg_st shape: expected {(len(qubits), len(frequencies), len(amp_values))}, got {xarray_data['shot_avg_st'].shape}"

    for i in range(shots):
        assert (xarray_data["shot_st"][i] == i).all(), f"shot_st[{i}]: expected all values to be {i}, got {xarray_data['shot_st'][i].values}"

    for f in frequencies:
        for a in amp_values:
            assert np.allclose(xarray_data["shot_avg_st"].sel(frequency=f, amp=a), a * f), f"shot_avg_st(frequency={f}, amp={a}): expected {a * f}, got {xarray_data['shot_avg_st'].sel(frequency=f, amp=a).values}"


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

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["shot_st"].dims == ("shot", "frequency"), f"shot_st dims: expected ('shot', 'frequency'), got {xarray_data['shot_st'].dims}"
    assert xarray_data["shot_st"].shape == (n_shots, len(frequencies)), f"shot_st shape: expected {(n_shots, len(frequencies))}, got {xarray_data['shot_st'].shape}"

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

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["amp_st"].dims == ("qubit", "amp"), f"amp_st dims: expected ('qubit', 'amp'), got {xarray_data['amp_st'].dims}"
    assert xarray_data["amp_st"].shape == (len(qubits), len(amp_values)), f"amp_st shape: expected {(len(qubits), len(amp_values))}, got {xarray_data['amp_st'].shape}"

    for a in amp_values:
        assert np.allclose(xarray_data["amp_st"].sel(amp=a), a), f"amp_st(amp={a}): expected {a}, got {xarray_data['amp_st'].sel(amp=a).values}"

    # Verify each native product combo maps to the correct value
    for q_idx, q in enumerate(qubits):
        for a_idx, a in enumerate(amp_values):
            assert np.allclose(xarray_data["amp_st"].sel(qubit=q, amp=a), a), f"amp_st(qubit={q}, amp={a}): expected {a}, got {xarray_data['amp_st'].sel(qubit=q, amp=a).values}"


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

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, sweep_list)

    assert xarray_data["shot_st"].dims == ("shot", "qubit", "frequency"), f"shot_st dims: expected ('shot', 'qubit', 'frequency'), got {xarray_data['shot_st'].dims}"
    assert xarray_data["shot_st"].shape == (10, len(qubits), len(frequencies)), f"shot_st shape: expected {(10, len(qubits), len(frequencies))}, got {xarray_data['shot_st'].shape}"

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

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["shot_st"].dims == ("shot", "qubit", "frequency", "amp"), f"shot_st dims: expected ('shot', 'qubit', 'frequency', 'amp'), got {xarray_data['shot_st'].dims}"
    assert xarray_data["freq_st"].dims == ("shot", "qubit", "frequency", "amp"), f"freq_st dims: expected ('shot', 'qubit', 'frequency', 'amp'), got {xarray_data['freq_st'].dims}"

    for i in range(n_shots):
        assert (xarray_data["shot_st"][i] == i).all(), f"shot_st[{i}]: expected all values to be {i}, got {xarray_data['shot_st'][i].values}"

    for f in frequencies:
        assert np.allclose(xarray_data["freq_st"].sel(frequency=f), f), f"freq_st(frequency={f}): expected all values to be {f}, got {xarray_data['freq_st'].sel(frequency=f).values}"


def test_coordinate_values(qmm):
    """Verify that xarray coordinate values match the original iterable values."""
    prod = make_product()
    with program() as prog:
        for args in prod:
            s = declare_with_stream(int, "shot_st")
            assign(s, args.shot)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert np.array_equal(xarray_data.coords["shot"].values, np.arange(shots)), f"shot coords: expected {np.arange(shots)}, got {xarray_data.coords['shot'].values}"
    assert np.array_equal(xarray_data.coords["qubit"].values, qubits), f"qubit coords: expected {qubits}, got {xarray_data.coords['qubit'].values}"
    assert np.allclose(xarray_data.coords["frequency"].values, frequencies), f"frequency coords: expected {frequencies}, got {xarray_data.coords['frequency'].values}"
    assert np.allclose(xarray_data.coords["amp"].values, amp_values), f"amp coords: expected {amp_values}, got {xarray_data.coords['amp'].values}"
