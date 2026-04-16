import numpy as np

from qm.qua import program, declare_with_stream, assign, fixed
from qm.qua.extensions.qua_iterators import QuaIterable, NativeIterable, QuaIterableRange, QuaProduct, NativeIterableRange, QuaZip

from tests.tests_qua_utilities.fetch_xarray_helpers import (
    frequencies, qubits, simulate_and_fetch, assert_dims_and_shape,
)


def test_qua_zip_native(qmm):
    native_zip_values = ["q1", "q2", "q3"]
    prod = QuaProduct([
        QuaIterableRange("shot", 10),
        QuaZip([
            NativeIterable("qubit", native_zip_values),
            NativeIterableRange("amp", 0.1, 0.4, 0.1),
        ], name="qb_amp"),
        QuaIterable("frequency", frequencies),
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(int, "val_st")
            assign(s, args.shot)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "val_st", ("shot", "qb_amp", "frequency"), (10, len(native_zip_values), len(frequencies)))

    for i in range(10):
        assert (xarray_data["val_st"][i] == i).all(), f"val_st[{i}]: expected all values to be {i}, got {xarray_data['val_st'][i].values}"


def test_qua_zip_qua(qmm):
    tau_values = np.linspace(1, 7, 5)
    prod = QuaProduct([
        QuaZip([
            QuaIterable("frequency", frequencies),
            QuaIterable("tau", tau_values),
        ], name="freq_tau"),
        NativeIterable("qubit", qubits),
    ])
    with program() as prog:
        for args in prod:
            s = declare_with_stream(fixed, "freq_st")
            assign(s, args.freq_tau.frequency)

    xarray_data = simulate_and_fetch(qmm, prog, prod)

    assert_dims_and_shape(xarray_data, "freq_st", ("freq_tau", "qubit"), (len(frequencies), len(qubits)))

    for i, f in enumerate(frequencies):
        assert np.allclose(xarray_data["freq_st"][i], f), f"freq_st[{i}]: expected all values to be {f}, got {xarray_data['freq_st'][i].values}"
