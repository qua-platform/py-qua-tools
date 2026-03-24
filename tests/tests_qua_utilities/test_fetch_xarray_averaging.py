import numpy as np

from qm.qua import program, declare_with_stream, assign
from qm.qua.extensions.qua_iterators.qua_native_iterators import NativeIterableBase

from qualang_tools.loops.qua_iterable_postprocess import fetch_xarray_data
from tests.tests_qua_utilities.conftest import config
from tests.tests_qua_utilities.fetch_xarray_helpers import (
    simulation_config, shots, frequencies, amp_values, qubits, make_product,
)


def test_full_average(qmm):
    prod = make_product()
    with program() as prog:
        for args in prod:
            full_avg = declare_with_stream(float, "full_avg_st", average_axes=[itr.name for itr in prod.iterables if not isinstance(itr, NativeIterableBase)])
            assign(full_avg, args.frequency * args.amp)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    assert xarray_data["full_avg_st"].dims == ("qubit", "amp"), f"full_avg_st dims: expected ('qubit', 'amp'), got {xarray_data['full_avg_st'].dims}"
    assert xarray_data["full_avg_st"].shape == (len(qubits), len(amp_values)), f"full_avg_st shape: expected {(len(qubits), len(amp_values))}, got {xarray_data['full_avg_st'].shape}"

    expected_per_amp = amp_values * np.mean(frequencies)
    for i, a in enumerate(amp_values):
        assert np.allclose(xarray_data["full_avg_st"].sel(amp=a), expected_per_amp[i]), f"full_avg_st(amp={a}): expected {expected_per_amp[i]}, got {xarray_data['full_avg_st'].sel(amp=a).values}"

    # Averaged-out coords (shot, frequency) should not appear in the dataset coords
    assert "shot" not in xarray_data.coords, f"'shot' should not be in coords after full averaging, got {list(xarray_data.coords)}"
    assert "frequency" not in xarray_data.coords, f"'frequency' should not be in coords after full averaging, got {list(xarray_data.coords)}"


def test_multiple_streams_different_averages(qmm):
    """Two streams: one averages shot only, the other averages both shot and frequency."""
    prod = make_product()
    with program() as prog:
        for args in prod:
            avg_shot = declare_with_stream(float, "avg_shot_st", average_axes=["shot"])
            avg_both = declare_with_stream(float, "avg_both_st", average_axes=["shot", "frequency"])
            assign(avg_shot, args.frequency * args.amp)
            assign(avg_both, args.frequency * args.amp)

    job = qmm.simulate(config, prog, simulation_config)
    job.result_handles.wait_for_all_values()
    xarray_data = fetch_xarray_data(job, prod)

    # avg_shot_st: shot averaged out → (qubit, frequency, amp)
    assert xarray_data["avg_shot_st"].dims == ("qubit", "frequency", "amp"), f"avg_shot_st dims: expected ('qubit', 'frequency', 'amp'), got {xarray_data['avg_shot_st'].dims}"
    assert xarray_data["avg_shot_st"].shape == (len(qubits), len(frequencies), len(amp_values)), f"avg_shot_st shape: expected {(len(qubits), len(frequencies), len(amp_values))}, got {xarray_data['avg_shot_st'].shape}"

    for f in frequencies:
        for a in amp_values:
            assert np.allclose(xarray_data["avg_shot_st"].sel(frequency=f, amp=a), a * f), f"avg_shot_st(frequency={f}, amp={a}): expected {a * f}, got {xarray_data['avg_shot_st'].sel(frequency=f, amp=a).values}"

    # avg_both_st: shot and frequency averaged out → (qubit, amp)
    assert xarray_data["avg_both_st"].dims == ("qubit", "amp"), f"avg_both_st dims: expected ('qubit', 'amp'), got {xarray_data['avg_both_st'].dims}"
    assert xarray_data["avg_both_st"].shape == (len(qubits), len(amp_values)), f"avg_both_st shape: expected {(len(qubits), len(amp_values))}, got {xarray_data['avg_both_st'].shape}"

    expected_per_amp = amp_values * np.mean(frequencies)
    for i, a in enumerate(amp_values):
        assert np.allclose(xarray_data["avg_both_st"].sel(amp=a), expected_per_amp[i]), f"avg_both_st(amp={a}): expected {expected_per_amp[i]}, got {xarray_data['avg_both_st'].sel(amp=a).values}"
