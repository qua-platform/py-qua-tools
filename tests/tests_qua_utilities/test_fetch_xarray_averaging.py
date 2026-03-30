import numpy as np

from qm.qua import program, declare_with_stream, assign
from qm.qua.extensions.qua_iterators.qua_native_iterators import NativeIterableBase

from tests.tests_qua_utilities.fetch_xarray_helpers import (
    frequencies, amp_values, qubits, make_product, simulate_and_fetch,
    assert_dims_and_shape, assert_allclose_sel,
)


def test_full_average(qmm):
    prod = make_product()
    with program() as prog:
        for args in prod:
            full_avg = declare_with_stream(float, "full_avg_st", average_axes=[itr.name for itr in prod.iterables if not isinstance(itr, NativeIterableBase)])
            assign(full_avg, args.frequency * args.amp)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "full_avg_st", ("qubit", "amp"), (len(qubits), len(amp_values)))

    expected_per_amp = amp_values * np.mean(frequencies)
    for i, a in enumerate(amp_values):
        assert_allclose_sel(xarray_data, "full_avg_st", expected_per_amp[i], amp=a)

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

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    # avg_shot_st: shot averaged out → (qubit, frequency, amp)
    assert_dims_and_shape(xarray_data, "avg_shot_st", ("qubit", "frequency", "amp"), (len(qubits), len(frequencies), len(amp_values)))

    for f in frequencies:
        for a in amp_values:
            assert_allclose_sel(xarray_data, "avg_shot_st", a * f, frequency=f, amp=a)

    # avg_both_st: shot and frequency averaged out → (qubit, amp)
    assert_dims_and_shape(xarray_data, "avg_both_st", ("qubit", "amp"), (len(qubits), len(amp_values)))

    expected_per_amp = amp_values * np.mean(frequencies)
    for i, a in enumerate(amp_values):
        assert_allclose_sel(xarray_data, "avg_both_st", expected_per_amp[i], amp=a)
